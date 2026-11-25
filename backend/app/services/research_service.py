"""Research service: Job lifecycle management, asynchronous LangGraph execution, and DB persistence."""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.models import (
    ResearchJob,
    ResearchTask,
    ResearchSource,
    ResearchClaim,
    AgentExecutionLog,
    ResearchReport,
)
from app.schemas.research import ResearchCreateRequest
from app.graph.workflow import research_workflow
from app.graph.state import ResearchState
from app.utils.logging import logger
from app.utils.citations import extract_in_text_citations

# Global registry of active background asyncio tasks for cancellation support
ACTIVE_TASKS: Dict[str, asyncio.Task] = {}


class ResearchService:
    """Orchestrates job persistence and background LangGraph agent execution."""

    @staticmethod
    def create_job(db: Session, req: ResearchCreateRequest) -> ResearchJob:
        """Create a new research job in the database with status 'queued'."""
        job = ResearchJob(
            research_question=req.research_question,
            status="queued",
            depth=req.depth,
            max_sources=req.max_sources,
            current_iteration=0,
            max_iterations=req.max_iterations,
            execution_metadata={
                "requested_depth": req.depth,
                "max_sources": req.max_sources,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info("Created new research job %s: '%s'", job.id, job.research_question[:50])
        return job

    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[ResearchJob]:
        return db.query(ResearchJob).filter(ResearchJob.id == job_id).first()

    @staticmethod
    def get_history(db: Session, limit: int = 50, offset: int = 0) -> List[ResearchJob]:
        return (
            db.query(ResearchJob)
            .order_by(ResearchJob.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete_job(db: Session, job_id: str) -> bool:
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            return False
        # Cancel if currently running
        if job_id in ACTIVE_TASKS:
            task = ACTIVE_TASKS[job_id]
            task.cancel()
            del ACTIVE_TASKS[job_id]
        db.delete(job)
        db.commit()
        logger.info("Deleted research job %s", job_id)
        return True

    @staticmethod
    def cancel_job(db: Session, job_id: str) -> bool:
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            return False

        if job_id in ACTIVE_TASKS:
            task = ACTIVE_TASKS[job_id]
            task.cancel()
            del ACTIVE_TASKS[job_id]

        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        db.commit()
        logger.info("Cancelled research job %s", job_id)
        return True

    @staticmethod
    async def run_research_workflow_async(job_id: str):
        """
        Background task executing the LangGraph workflow and streaming/persisting
        intermediate state into PostgreSQL / SQLite.
        """
        logger.info("Starting background LangGraph workflow execution for job %s", job_id)
        db = SessionLocal()
        try:
            job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
            if not job:
                logger.error("Job %s not found in database for background execution.", job_id)
                return

            job.status = "planning"
            db.commit()

            initial_state: ResearchState = {
                "research_id": job.id,
                "research_question": job.research_question,
                "depth": job.depth,
                "max_sources": job.max_sources,
                "current_iteration": 0,
                "max_iterations": job.max_iterations,
                "plan": None,
                "sources": [],
                "analysis": None,
                "fact_check": None,
                "review": None,
                "report": None,
                "current_agent": "Supervisor",
                "status": "planning",
                "agent_logs": [],
                "error": None
            }

            # Execute LangGraph workflow nodes
            current_state = initial_state
            async for step_output in research_workflow.astream(initial_state):
                # step_output is a dictionary keyed by node name (e.g. {"supervisor": {...}})
                for node_name, node_state_delta in step_output.items():
                    # Update local state
                    current_state.update(node_state_delta)
                    job_status = node_state_delta.get("status", current_state.get("status", "running"))
                    current_agent = node_state_delta.get("current_agent", node_name.title())

                    logger.info("Workflow node '%s' completed for job %s (status=%s)", node_name, job_id, job_status)

                    # Update database job status
                    job.status = job_status
                    job.current_iteration = current_state.get("current_iteration", 0)

                    # Persist newly recorded agent execution logs
                    if "agent_logs" in node_state_delta and node_state_delta["agent_logs"]:
                        for log_dict in node_state_delta["agent_logs"]:
                            log_rec = AgentExecutionLog(
                                research_id=job.id,
                                agent_name=log_dict.get("agent_name", current_agent),
                                input_summary=log_dict.get("input_summary"),
                                output_summary=log_dict.get("output_summary"),
                                status=log_dict.get("status", "completed"),
                                execution_time=float(log_dict.get("execution_time", 0.0)),
                                error_message=log_dict.get("error_message")
                            )
                            db.add(log_rec)

                    # If supervisor completed, persist planned tasks
                    if node_name == "supervisor" and current_state.get("plan"):
                        plan = current_state["plan"]
                        for p_idx, sub in enumerate(plan.subtopics, 1):
                            task_rec = ResearchTask(
                                research_id=job.id,
                                task_description=f"Investigate {sub.title} ({', '.join(sub.search_queries[:2])})",
                                assigned_agent="Researcher",
                                status="in_progress",
                                priority=sub.priority,
                                subtopic=sub.title
                            )
                            db.add(task_rec)

                    # If researcher completed, persist unique sources
                    if node_name == "researcher" and "sources" in node_state_delta:
                        new_sources = node_state_delta["sources"]
                        for s_idx, ev in enumerate(new_sources, 1):
                            existing_src = (
                                db.query(ResearchSource)
                                .filter(
                                    ResearchSource.research_id == job.id,
                                    ResearchSource.canonical_url == ev.canonical_url
                                )
                                .first()
                            )
                            if not existing_src:
                                src_rec = ResearchSource(
                                    research_id=job.id,
                                    title=ev.title,
                                    url=ev.url,
                                    canonical_url=ev.canonical_url,
                                    domain=ev.domain,
                                    publication_date=ev.publication_date,
                                    extracted_content=ev.extracted_content,
                                    relevance_score=ev.relevance_score,
                                    is_canonical=True,
                                    citation_number=len(db.query(ResearchSource).filter(ResearchSource.research_id == job.id).all()) + 1
                                )
                                db.add(src_rec)

                    # If fact-checker completed, persist claims
                    if node_name == "fact_checker" and current_state.get("fact_check"):
                        fc = current_state["fact_check"]
                        for c in fc.claims:
                            claim_rec = ResearchClaim(
                                research_id=job.id,
                                claim_text=c.claim_text,
                                verification_status=c.verification_status,
                                supporting_source_ids=c.supporting_citation_numbers,
                                confidence=c.confidence,
                                reasoning=c.reasoning
                            )
                            db.add(claim_rec)

                    # If report generator completed, persist final report
                    if node_name == "report_generator" and current_state.get("report"):
                        rep = current_state["report"]
                        job.final_report = rep.markdown_full_report
                        job.status = "completed"
                        job.completed_at = datetime.utcnow()

                        report_rec = ResearchReport(
                            research_id=job.id,
                            report_content=rep.markdown_full_report,
                            executive_summary=rep.executive_summary,
                            methodology=rep.methodology,
                            key_findings=rep.key_findings,
                            risks_opportunities=rep.risks_and_opportunities,
                            limitations=rep.limitations,
                            citations_json=[c.model_dump() for c in rep.citations]
                        )
                        db.add(report_rec)

                        # Update all subtasks to completed
                        db.query(ResearchTask).filter(ResearchTask.research_id == job.id).update({"status": "completed"})

                    db.commit()

            logger.info("LangGraph workflow successfully finished for job %s", job_id)

        except asyncio.CancelledError:
            logger.warning("Workflow task for job %s was cancelled.", job_id)
            job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
            if job:
                job.status = "cancelled"
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception as exc:
            logger.error("Unhandled error in workflow execution for job %s: %s", job_id, exc, exc_info=True)
            job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                db.commit()
        finally:
            if job_id in ACTIVE_TASKS:
                del ACTIVE_TASKS[job_id]
            db.close()
