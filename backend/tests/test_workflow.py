"""End-to-End Test of the LangGraph Multi-Agent Research Workflow."""

import pytest
from app.graph.workflow import research_workflow
from app.graph.state import ResearchState


@pytest.mark.asyncio
async def test_full_langgraph_research_workflow():
    """Execute complete multi-agent workflow from START to END."""
    initial_state: ResearchState = {
        "research_id": "test-e2e-001",
        "research_question": "Analyse the impact of generative AI on software engineering jobs over the next five years.",
        "depth": "quick",
        "max_sources": 6,
        "current_iteration": 0,
        "max_iterations": 2,
        "plan": None,
        "sources": [],
        "analysis": None,
        "fact_check": None,
        "review": None,
        "report": None,
        "current_agent": "Supervisor",
        "status": "queued",
        "agent_logs": [],
        "error": None
    }

    final_state = await research_workflow.ainvoke(initial_state)

    # 1. Check final terminal status
    assert final_state["status"] == "completed"
    assert final_state["error"] is None

    # 2. Check deliverables produced by all 6 agents
    # Supervisor
    assert final_state["plan"] is not None
    assert len(final_state["plan"].subtopics) >= 2

    # Researcher
    assert len(final_state["sources"]) >= 1
    for src in final_state["sources"]:
        assert src.canonical_url != ""
        assert src.domain != ""

    # Analyst
    assert final_state["analysis"] is not None
    assert len(final_state["analysis"].findings) >= 1

    # Fact-Checker
    assert final_state["fact_check"] is not None
    assert len(final_state["fact_check"].claims) >= 1

    # Reviewer
    assert final_state["review"] is not None
    assert final_state["current_iteration"] >= 1

    # Report Generator
    assert final_state["report"] is not None
    report = final_state["report"]
    assert report.title != ""
    assert report.executive_summary != ""
    assert "## References" in report.markdown_full_report or "## Sources" in report.markdown_full_report
    assert len(report.citations) >= 1

    # 3. Check agent execution logs telemetry
    assert len(final_state["agent_logs"]) >= 6
    agent_names_logged = {log["agent_name"] for log in final_state["agent_logs"]}
    assert "Supervisor" in agent_names_logged
    assert "Researcher" in agent_names_logged
    assert "Analyst" in agent_names_logged
    assert "Fact Checker" in agent_names_logged
    assert "Reviewer" in agent_names_logged
    assert "Report Generator" in agent_names_logged
