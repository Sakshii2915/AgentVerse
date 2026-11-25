"""Strongly typed LangGraph state definition for the multi-agent research workflow."""

from typing import List, Dict, Any, Optional, Annotated
import operator
from typing_extensions import TypedDict

from app.schemas.agents import (
    SupervisorPlanOutput,
    ExtractedEvidence,
    AnalystOutput,
    FactCheckerOutput,
    ReviewerOutput,
    ReportGeneratorOutput,
)


def merge_sources(existing: List[ExtractedEvidence], new_items: List[ExtractedEvidence]) -> List[ExtractedEvidence]:
    """Reducer that merges new evidence sources while maintaining canonical uniqueness."""
    seen_canonicals = {s.canonical_url for s in existing}
    combined = list(existing)
    for item in new_items:
        if item.canonical_url not in seen_canonicals:
            combined.append(item)
            seen_canonicals.add(item.canonical_url)
    return combined


class AgentLogEntry(TypedDict):
    agent_name: str
    status: str  # started, completed, failed
    execution_time: float
    input_summary: str
    output_summary: str
    error_message: Optional[str]
    timestamp: str


class ResearchState(TypedDict):
    """
    Central shared state object passed across nodes in the LangGraph StateGraph.
    """
    research_id: str
    research_question: str
    depth: str
    max_sources: int
    current_iteration: int
    max_iterations: int

    # Agent structured deliverables
    plan: Optional[SupervisorPlanOutput]
    sources: Annotated[List[ExtractedEvidence], merge_sources]
    analysis: Optional[AnalystOutput]
    fact_check: Optional[FactCheckerOutput]
    review: Optional[ReviewerOutput]
    report: Optional[ReportGeneratorOutput]

    # Workflow execution telemetry
    current_agent: str
    status: str  # queued, planning, researching, analyzing, fact_checking, reviewing, generating_report, completed, failed
    agent_logs: Annotated[List[Dict[str, Any]], operator.add]
    error: Optional[str]
