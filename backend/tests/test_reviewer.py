"""Test Reviewer Agent and Routing."""

import pytest
from app.agents.reviewer import ReviewerAgent
from app.graph.routing import route_after_review
from app.schemas.agents import (
    AnalystOutput,
    FactCheckerOutput,
    ReviewerOutput,
    ExtractedEvidence
)


@pytest.mark.asyncio
async def test_reviewer_evaluation(mock_llm):
    agent = ReviewerAgent(llm=mock_llm)
    analyst_out = AnalystOutput(summary_of_evidence="Evidence collected.")
    fact_out = FactCheckerOutput(overall_credibility_score=0.9)
    sources = []

    review = await agent.review(
        research_question="Generative AI Impact",
        analyst_output=analyst_out,
        fact_checker_output=fact_out,
        sources=sources,
        current_iteration=1,
        max_iterations=2
    )

    assert isinstance(review, ReviewerOutput)
    assert review.route_decision in ("report_generator", "researcher", "analyst")
    assert 0.0 <= review.completeness_score <= 1.0


@pytest.mark.asyncio
async def test_reviewer_max_iteration_enforcement(mock_llm):
    """Verify that reaching max_iterations forces routing to report_generator."""
    agent = ReviewerAgent(llm=mock_llm)
    analyst_out = AnalystOutput(summary_of_evidence="Evidence collected.")
    fact_out = FactCheckerOutput(overall_credibility_score=0.5)

    review = await agent.review(
        research_question="Generative AI Impact",
        analyst_output=analyst_out,
        fact_checker_output=fact_out,
        sources=[],
        current_iteration=2,
        max_iterations=2
    )

    assert review.route_decision == "report_generator"
    assert review.is_sufficient is True


def test_route_after_review_conditional_routing():
    """Test graph edge router function."""
    state_max = {
        "current_iteration": 2,
        "max_iterations": 2,
        "review": ReviewerOutput(
            is_sufficient=False,
            route_decision="researcher",
            completeness_score=0.4,
            citation_coverage_score=0.3,
            critique_feedback="More data needed"
        )
    }
    # Should force report_generator due to hard upper iteration bound
    assert route_after_review(state_max) == "report_generator"

    state_researcher = {
        "current_iteration": 0,
        "max_iterations": 2,
        "review": ReviewerOutput(
            is_sufficient=False,
            route_decision="researcher",
            completeness_score=0.4,
            citation_coverage_score=0.3,
            critique_feedback="Missing security angle",
            targeted_queries_for_researcher=["ai code security vulnerabilities"]
        )
    }
    assert route_after_review(state_researcher) == "researcher"
