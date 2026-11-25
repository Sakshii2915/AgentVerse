"""Test Fact-Checker Agent."""

import pytest
from app.agents.fact_checker import FactCheckerAgent
from app.schemas.agents import (
    FactCheckerOutput,
    AnalystOutput,
    AnalystFinding,
    ExtractedEvidence
)


@pytest.mark.asyncio
async def test_fact_checker_claim_auditing(mock_llm):
    agent = FactCheckerAgent(llm=mock_llm)
    analyst_out = AnalystOutput(
        findings=[
            AnalystFinding(
                statement="Developer velocity improves significantly with AI.",
                evidence_type="direct_fact"
            )
        ],
        summary_of_evidence="Positive empirical results."
    )
    sources = [
        ExtractedEvidence(
            url="https://research.example.org/1",
            canonical_url="https://research.example.org/1",
            title="Benchmark 2024",
            domain="research.example.org",
            extracted_content="Evidence shows 20% to 55% speed improvement.",
            relevance_score=0.9,
            subtopic="Productivity"
        )
    ]

    result = await agent.verify(
        research_question="Impact of GenAI on Software Engineering",
        analyst_output=analyst_out,
        sources=sources
    )

    assert isinstance(result, FactCheckerOutput)
    assert len(result.claims) >= 1
    for claim in result.claims:
        assert claim.verification_status in ("supported", "partially_supported", "contradicted", "unverified")
        assert 0.0 <= claim.confidence <= 1.0
        assert claim.claim_text != ""
