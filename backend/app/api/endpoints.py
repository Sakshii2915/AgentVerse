"""FastAPI REST API router and route handlers for AgentVerse."""

import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Response
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.models import (
    ResearchJob,
    ResearchTask,
    ResearchSource,
    ResearchClaim,
    AgentExecutionLog,
    ResearchReport,
)
from app.schemas.research import (
    ResearchCreateRequest,
    ResearchJobResponse,
    ResearchJobDetailResponse,
    ResearchSourceSchema,
    ResearchClaimSchema,
    AgentExecutionLogSchema,
    ResearchReportSchema,
    ResearchHistoryItem,
    SystemHealthResponse,
)
from app.services.research_service import ResearchService, ACTIVE_TASKS
from app.services.report_service import ReportService
from app.utils.logging import logger

router = APIRouter(prefix="/api", tags=["Research Operations"])


@router.get("/health", response_model=SystemHealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Return backend health and service provider configuration status."""
    db_ok = True
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        db_ok = False

    return SystemHealthResponse(
        status="healthy" if db_ok else "degraded",
        version=settings.VERSION,
        search_provider=settings.effective_search_provider,
        openai_configured=settings.is_openai_configured,
        tavily_configured=settings.is_tavily_configured,
        database_connected=db_ok
    )


@router.post("/research", response_model=ResearchJobResponse, status_code=201)
async def create_research(
    payload: ResearchCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Accept a research question, initiate the multi-agent mission,
    and trigger the LangGraph workflow in the background.
    """
    job = ResearchService.create_job(db=db, req=payload)

    # Spawn background task
    async def _run_job():
        try:
            await ResearchService.run_research_workflow_async(job.id)
        except Exception as e:
            logger.error("Background task error for %s: %s", job.id, e)

    task = asyncio.create_task(_run_job())
    ACTIVE_TASKS[job.id] = task

    return job


@router.get("/research/history", response_model=List[ResearchHistoryItem])
def get_research_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Return list of previous research jobs with source and claim counters."""
    jobs = ResearchService.get_history(db=db, limit=limit, offset=offset)
    history_items = []
    for j in jobs:
        src_count = len(j.sources)
        claim_count = len(j.claims)
        has_rep = bool(j.reports or j.final_report)
        history_items.append(
            ResearchHistoryItem(
                id=j.id,
                research_question=j.research_question,
                status=j.status,
                depth=j.depth,
                source_count=src_count,
                claim_count=claim_count,
                created_at=j.created_at,
                completed_at=j.completed_at,
                has_report=has_rep
            )
        )
    return history_items


@router.get("/research/history/{research_id}", response_model=ResearchJobDetailResponse)
def get_history_detail(research_id: str, db: Session = Depends(get_db)):
    """Return full research mission details, tasks, sources, claims, and reports."""
    job = ResearchService.get_job(db=db, job_id=research_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Research job '{research_id}' not found.")

    latest_report = job.reports[0] if job.reports else None
    return ResearchJobDetailResponse(
        id=job.id,
        research_question=job.research_question,
        status=job.status,
        depth=job.depth,
        max_sources=job.max_sources,
        current_iteration=job.current_iteration,
        max_iterations=job.max_iterations,
        created_at=job.created_at,
        completed_at=job.completed_at,
        final_report=job.final_report,
        execution_metadata=job.execution_metadata,
        tasks=[ResearchTaskSchema.model_validate(t) for t in job.tasks],
        sources=[ResearchSourceSchema.model_validate(s) for s in job.sources],
        claims=[ResearchClaimSchema.model_validate(c) for c in job.claims],
        logs=[AgentExecutionLogSchema.model_validate(l) for l in job.logs],
        report=ResearchReportSchema.model_validate(latest_report) if latest_report else None
    )


@router.delete("/research/history/{research_id}")
def delete_history_item(research_id: str, db: Session = Depends(get_db)):
    """Delete a research session and its associated data."""
    success = ResearchService.delete_job(db=db, job_id=research_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Research job '{research_id}' not found.")
    return {"message": f"Research job '{research_id}' deleted successfully."}


@router.get("/research/{research_id}", response_model=ResearchJobResponse)
def get_research_status(research_id: str, db: Session = Depends(get_db)):
    """Return current status and progress for a research job."""
    job = ResearchService.get_job(db=db, job_id=research_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Research job '{research_id}' not found.")
    return job


@router.get("/research/{research_id}/report", response_model=ResearchReportSchema)
def get_research_report(research_id: str, db: Session = Depends(get_db)):
    """Return the completed synthesis report."""
    report = ReportService.get_report_by_job_id(db=db, job_id=research_id)
    if not report:
        job = ResearchService.get_job(db=db, job_id=research_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Research job '{research_id}' not found.")
        if job.status in ("queued", "planning", "researching", "analyzing", "fact_checking", "reviewing", "generating_report"):
            raise HTTPException(status_code=202, detail="Report generation still in progress.")
        raise HTTPException(status_code=404, detail="No report generated for this research job.")
    return report


@router.get("/research/{research_id}/report/pdf")
def download_report_pdf(research_id: str, db: Session = Depends(get_db)):
    """Generate and return downloadable PDF research report."""
    pdf_bytes = ReportService.generate_pdf(db=db, job_id=research_id)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="PDF report could not be generated or job is incomplete.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=AgentVerse_Report_{research_id[:8]}.pdf"
        }
    )


@router.get("/research/{research_id}/sources", response_model=List[ResearchSourceSchema])
def get_research_sources(research_id: str, db: Session = Depends(get_db)):
    """Return all evidence sources retrieved and deduplicated for this research job."""
    job = ResearchService.get_job(db=db, job_id=research_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Research job '{research_id}' not found.")
    return [ResearchSourceSchema.model_validate(s) for s in job.sources]


@router.get("/research/{research_id}/agents", response_model=List[AgentExecutionLogSchema])
def get_agent_logs(research_id: str, db: Session = Depends(get_db)):
    """Return telemetry logs for all agents participating in this research job."""
    job = ResearchService.get_job(db=db, job_id=research_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Research job '{research_id}' not found.")
    return [AgentExecutionLogSchema.model_validate(l) for l in job.logs]


@router.post("/research/{research_id}/cancel")
def cancel_research(research_id: str, db: Session = Depends(get_db)):
    """Cancel a currently active research job."""
    success = ResearchService.cancel_job(db=db, job_id=research_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Research job '{research_id}' not found.")
    return {"message": f"Research job '{research_id}' was cancelled."}
