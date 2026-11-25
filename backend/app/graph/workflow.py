"""LangGraph multi-agent research workflow graph compilation."""

from langgraph.graph import StateGraph, START, END
from app.graph.state import ResearchState
from app.graph.nodes import (
    supervisor_node,
    researcher_node,
    analyst_node,
    fact_checker_node,
    reviewer_node,
    report_generator_node,
)
from app.graph.routing import route_after_review
from app.utils.logging import logger


def build_research_graph() -> StateGraph:
    """Construct and compile the multi-agent StateGraph."""
    logger.info("Building AgentVerse LangGraph StateGraph workflow...")

    workflow = StateGraph(ResearchState)

    # 1. Register specialized agent nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("fact_checker", fact_checker_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("report_generator", report_generator_node)

    # 2. Add sequential pipeline edges
    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", "researcher")
    workflow.add_edge("researcher", "analyst")
    workflow.add_edge("analyst", "fact_checker")
    workflow.add_edge("fact_checker", "reviewer")

    # 3. Add dynamic conditional edge from reviewer
    workflow.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "report_generator": "report_generator",
            "researcher": "researcher",
            "analyst": "analyst",
        }
    )

    # 4. Final report generator termination
    workflow.add_edge("report_generator", END)

    compiled = workflow.compile()
    logger.info("AgentVerse LangGraph workflow compiled successfully.")
    return compiled


# Module-level compiled workflow singleton
research_workflow = build_research_graph()
