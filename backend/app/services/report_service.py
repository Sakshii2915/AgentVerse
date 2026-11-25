"""Report service: formatting, export, and citation presentation."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import ResearchJob, ResearchReport, ResearchSource
from app.utils.pdf_export import generate_pdf_report
from app.utils.logging import logger


class ReportService:
    """Manages report queries, markdown extraction, and PDF generation."""

    @staticmethod
    def get_report_by_job_id(db: Session, job_id: str) -> Optional[ResearchReport]:
        return (
            db.query(ResearchReport)
            .filter(ResearchReport.research_id == job_id)
            .order_by(ResearchReport.created_at.desc())
            .first()
        )

    @staticmethod
    def generate_pdf(db: Session, job_id: str) -> Optional[bytes]:
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            return None

        report = (
            db.query(ResearchReport)
            .filter(ResearchReport.research_id == job_id)
            .order_by(ResearchReport.created_at.desc())
            .first()
        )
        if not report:
            return None

        sources = (
            db.query(ResearchSource)
            .filter(ResearchSource.research_id == job_id)
            .order_by(ResearchSource.citation_number)
            .all()
        )

        source_dicts = [
            {
                "citation_number": s.citation_number,
                "title": s.title,
                "domain": s.domain,
                "url": s.url,
                "publication_date": s.publication_date
            }
            for s in sources
        ]

        pdf_bytes = generate_pdf_report(
            title=f"Research Report: {job.research_question}",
            executive_summary=report.executive_summary,
            full_markdown=report.report_content,
            sources=source_dicts
        )
        return pdf_bytes
