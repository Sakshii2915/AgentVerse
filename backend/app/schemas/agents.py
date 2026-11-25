"""Structured agent input/output Pydantic schemas for multi-agent LangGraph workflow."""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


# --- Agent 1: Supervisor / Planner Schemas ---

class SubtopicPlan(BaseModel):
    title: str = Field(..., description="Clear title of the research subtopic.")
    search_queries: List[str] = Field(..., description="Targeted web search queries for this subtopic.")
    priority: int = Field(default=1, ge=1, le=5, description="Investigation priority (1=highest, 5=lowest).")
    target_aspects: List[str] = Field(default_factory=list, description="Specific questions or data points to locate.")


class SupervisorPlanOutput(BaseModel):
    domain: str = Field(..., description="Academic, technical, or business domain.")
    objective_summary: str = Field(..., description="Core objective distillation.")
    subtopics: List[SubtopicPlan] = Field(..., min_length=2, max_length=6, description="List of 3 to 6 subtopics.")
    strategic_rationale: str = Field(..., description="Why this decomposition answers the prompt.")


# --- Agent 2: Researcher Schemas ---

class ExtractedEvidence(BaseModel):
    url: str
    canonical_url: str
    title: str
    domain: str
    publication_date: Optional[str] = None
    extracted_content: str
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    subtopic: str


class ResearcherBatchOutput(BaseModel):
    sources: List[ExtractedEvidence] = Field(default_factory=list)
    search_notes: Optional[str] = None


# --- Agent 3: Analyst Schemas ---

class AnalystTrend(BaseModel):
    trend_name: str
    description: str
    evidence_basis: str


class AnalystFinding(BaseModel):
    statement: str
    evidence_type: Literal["direct_fact", "interpretation", "projection"]
    supporting_urls: List[str] = Field(default_factory=list)


class AnalystOutput(BaseModel):
    patterns_and_themes: List[str] = Field(default_factory=list)
    trends: List[AnalystTrend] = Field(default_factory=list)
    findings: List[AnalystFinding] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    risks_and_challenges: List[str] = Field(default_factory=list)
    research_gaps: List[str] = Field(default_factory=list)
    summary_of_evidence: str


# --- Agent 4: Fact-Checker Schemas ---

class VerifiedClaim(BaseModel):
    claim_text: str
    verification_status: Literal["supported", "partially_supported", "contradicted", "unverified"]
    supporting_citation_numbers: List[int] = Field(default_factory=list)
    supporting_urls: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    contradictory_evidence: Optional[str] = None


class FactCheckerOutput(BaseModel):
    claims: List[VerifiedClaim] = Field(default_factory=list)
    overall_credibility_score: float = Field(ge=0.0, le=1.0)
    unsupported_claims_summary: List[str] = Field(default_factory=list)
    contradictions_detected: List[str] = Field(default_factory=list)
    additional_research_needed: bool = False
    recommended_queries: List[str] = Field(default_factory=list)


# --- Agent 5: Report Generator Schemas ---

class CitationItem(BaseModel):
    number: int
    title: str
    url: str
    domain: str
    publication_date: Optional[str] = None


class ReportSection(BaseModel):
    heading: str
    content: str


class ReportGeneratorOutput(BaseModel):
    title: str
    executive_summary: str
    methodology: str
    key_findings: List[str]
    detailed_analysis: str
    risks_and_opportunities: Dict[str, List[str]]
    limitations: str
    conclusion: str
    markdown_full_report: str
    citations: List[CitationItem]


# --- Agent 6: Reviewer Schemas ---

class ReviewerOutput(BaseModel):
    is_sufficient: bool = Field(..., description="Whether evidence is comprehensive enough for final synthesis.")
    route_decision: Literal["report_generator", "researcher", "analyst"] = Field(
        ...,
        description="Where to route the graph next based on rigorous evaluation."
    )
    completeness_score: float = Field(ge=0.0, le=1.0, description="Overall completeness score from 0.0 to 1.0.")
    citation_coverage_score: float = Field(ge=0.0, le=1.0, description="Proportion of key claims backed by evidence.")
    critique_feedback: str = Field(..., description="Actionable critique for next steps.")
    missing_aspects: List[str] = Field(default_factory=list, description="Specific topics needing further research.")
    targeted_queries_for_researcher: List[str] = Field(default_factory=list, description="Specific queries if routing to researcher.")
