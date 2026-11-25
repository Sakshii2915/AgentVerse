"""SQLAlchemy Database Models for AgentVerse."""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    """Generate string UUID."""
    return str(uuid.uuid4())


class ResearchJob(Base):
    """Represents an overall research mission submitted by the user."""
    __tablename__ = "research_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    research_question = Column(Text, nullable=False)
    status = Column(String(50), default="queued", index=True)
    depth = Column(String(20), default="standard")
    max_sources = Column(Integer, default=10)
    current_iteration = Column(Integer, default=0)
    max_iterations = Column(Integer, default=2)
    final_report = Column(Text, nullable=True)
    execution_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    tasks = relationship("ResearchTask", back_populates="job", cascade="all, delete-orphan", order_by="ResearchTask.created_at")
    sources = relationship("ResearchSource", back_populates="job", cascade="all, delete-orphan", order_by="ResearchSource.citation_number")
    claims = relationship("ResearchClaim", back_populates="job", cascade="all, delete-orphan", order_by="ResearchClaim.created_at")
    logs = relationship("AgentExecutionLog", back_populates="job", cascade="all, delete-orphan", order_by="AgentExecutionLog.created_at")
    reports = relationship("ResearchReport", back_populates="job", cascade="all, delete-orphan", order_by="ResearchReport.created_at.desc()")


class ResearchTask(Base):
    """Sub-task planned by Supervisor agent."""
    __tablename__ = "research_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    research_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    task_description = Column(Text, nullable=False)
    assigned_agent = Column(String(50), nullable=False)
    status = Column(String(50), default="pending", index=True)  # pending, in_progress, completed, failed
    priority = Column(Integer, default=1)
    subtopic = Column(String(255), nullable=True)
    findings = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("ResearchJob", back_populates="tasks")


class ResearchSource(Base):
    """Collected evidence source with metadata and canonical deduplication."""
    __tablename__ = "research_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    research_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    canonical_url = Column(Text, nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    publication_date = Column(String(100), nullable=True)
    extracted_content = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0.5)
    is_canonical = Column(Boolean, default=True)
    citation_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("ResearchJob", back_populates="sources")


class ResearchClaim(Base):
    """Factual statements extracted and verified by the Fact-Checker agent."""
    __tablename__ = "research_claims"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    research_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    claim_text = Column(Text, nullable=False)
    # Statuses: supported, partially_supported, contradicted, unverified
    verification_status = Column(String(50), default="unverified", index=True)
    supporting_source_ids = Column(JSON, default=list)  # list of source IDs or citation numbers
    confidence = Column(Float, default=0.0)
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("ResearchJob", back_populates="claims")


class AgentExecutionLog(Base):
    """Execution timeline and telemetry for individual agents."""
    __tablename__ = "agent_execution_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    research_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    agent_name = Column(String(50), nullable=False, index=True)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    status = Column(String(50), default="started")  # started, completed, failed
    execution_time = Column(Float, default=0.0)  # seconds
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("ResearchJob", back_populates="logs")


class ResearchReport(Base):
    """Final synthesis generated by the Report Generator agent."""
    __tablename__ = "research_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    research_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    report_content = Column(Text, nullable=False)
    executive_summary = Column(Text, nullable=False)
    methodology = Column(Text, nullable=True)
    key_findings = Column(JSON, nullable=True)
    risks_opportunities = Column(JSON, nullable=True)
    limitations = Column(Text, nullable=True)
    citations_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("ResearchJob", back_populates="reports")
