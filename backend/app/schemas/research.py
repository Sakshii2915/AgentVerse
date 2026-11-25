"""Pydantic schemas for research jobs, sources, claims, and reports."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ResearchCreateRequest(BaseModel):
    """Payload to initiate a new research job."""
    research_question: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="The research topic or analytical question to investigate."
    )
    depth: str = Field(
        default="standard",
        description="Research thoroughness: 'quick' (3 sources/subtopic), 'standard' (5), or 'deep' (8)."
    )
    max_sources: int = Field(
        default=12,
        ge=3,
        le=30,
        description="Maximum total canonical sources to aggregate across subtopics."
    )
    max_iterations: int = Field(
        default=2,
        ge=1,
        le=4,
        description="Maximum number of research-reviewer revision loops."
    )


class ResearchTaskSchema(BaseModel):
    id: str
    research_id: str
    task_description: str
    assigned_agent: str
    status: str
    priority: int
    subtopic: Optional[str] = None
    findings: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchSourceSchema(BaseModel):
    id: str
    research_id: str
    title: str
    url: str
    domain: str
    publication_date: Optional[str] = None
    extracted_content: str
    relevance_score: float
    is_canonical: bool
    citation_number: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchClaimSchema(BaseModel):
    id: str
    research_id: str
    claim_text: str
    verification_status: str  # supported, partially_supported, contradicted, unverified
    supporting_source_ids: List[Any] = Field(default_factory=list)
    confidence: float
    reasoning: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentExecutionLogSchema(BaseModel):
    id: str
    research_id: str
    agent_name: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    status: str
    execution_time: float
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchReportSchema(BaseModel):
    id: str
    research_id: str
    report_content: str
    executive_summary: str
    methodology: Optional[str] = None
    key_findings: Optional[Any] = None
    risks_opportunities: Optional[Any] = None
    limitations: Optional[str] = None
    citations_json: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchJobResponse(BaseModel):
    id: str
    research_question: str
    status: str
    depth: str
    max_sources: int
    current_iteration: int
    max_iterations: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    final_report: Optional[str] = None
    execution_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ResearchJobDetailResponse(ResearchJobResponse):
    tasks: List[ResearchTaskSchema] = Field(default_factory=list)
    sources: List[ResearchSourceSchema] = Field(default_factory=list)
    claims: List[ResearchClaimSchema] = Field(default_factory=list)
    logs: List[AgentExecutionLogSchema] = Field(default_factory=list)
    report: Optional[ResearchReportSchema] = None


class ResearchHistoryItem(BaseModel):
    id: str
    research_question: str
    status: str
    depth: str
    source_count: int
    claim_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    has_report: bool


class SystemHealthResponse(BaseModel):
    status: str
    version: str
    search_provider: str
    openai_configured: bool
    tavily_configured: bool
    database_connected: bool
