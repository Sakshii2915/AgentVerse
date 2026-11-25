"""Test Supervisor / Planner Agent."""

import pytest
from app.agents.supervisor import SupervisorAgent
from app.schemas.agents import SupervisorPlanOutput


@pytest.mark.asyncio
async def test_supervisor_planning(mock_llm):
    agent = SupervisorAgent(llm=mock_llm)
    plan = await agent.plan(
        research_question="Analyse the impact of generative AI on software engineering jobs over the next five years.",
        depth="standard"
    )

    assert isinstance(plan, SupervisorPlanOutput)
    assert plan.domain != ""
    assert 2 <= len(plan.subtopics) <= 6

    for sub in plan.subtopics:
        assert sub.title != ""
        assert len(sub.search_queries) >= 1
        assert 1 <= sub.priority <= 5
