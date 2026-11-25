"""Test Analyst Agent."""

import pytest
from app.agents.analyst import AnalystAgent
from app.schemas.agents import AnalystOutput, ExtractedEvidence


@pytest.mark.asyncio
async def test_analyst_evaluation(mock_llm):
    agent = AnalystAgent(llm=mock_llm)
    sources = [
        ExtractedEvidence(
            url="https://research.example.org/study-1",
            canonical_url="https://research.example.org/study-1",
            title="AI Impact on Developers",
            domain="research.example.org",
            extracted_content="Empirical research shows 30% speedup in standard task coding.",
            relevance_score=0.9,
            subtopic="Productivity"
        )
    ]

    analysis = await agent.analyze(
        research_question="Impact of GenAI on Software Engineering",
        sources=sources
    )

    assert isinstance(analysis, AnalystOutput)
    assert len(analysis.findings) >= 1
    # Check that findings have valid evidence_type
    for f in analysis.findings:
        assert f.evidence_type in ("direct_fact", "interpretation", "projection")
    assert len(analysis.trends) >= 1
    assert len(analysis.opportunities) >= 1
    assert len(analysis.risks_and_challenges) >= 1
