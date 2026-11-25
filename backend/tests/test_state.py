"""Test LangGraph ResearchState and reducers."""

import pytest
from app.graph.state import ResearchState, merge_sources
from app.schemas.agents import ExtractedEvidence


def test_merge_sources_deduplication():
    """Verify that merge_sources preserves unique sources based on canonical_url."""
    s1 = ExtractedEvidence(
        url="https://example.com/article1?utm_source=twitter",
        canonical_url="https://example.com/article1",
        title="Article 1",
        domain="example.com",
        extracted_content="Content 1",
        relevance_score=0.9,
        subtopic="Topic A"
    )
    s2 = ExtractedEvidence(
        url="https://example.com/article2",
        canonical_url="https://example.com/article2",
        title="Article 2",
        domain="example.com",
        extracted_content="Content 2",
        relevance_score=0.8,
        subtopic="Topic A"
    )
    # Duplicate with same canonical URL
    s3 = ExtractedEvidence(
        url="https://example.com/article1?fbclid=xyz",
        canonical_url="https://example.com/article1",
        title="Article 1 Duplicate",
        domain="example.com",
        extracted_content="Different text",
        relevance_score=0.7,
        subtopic="Topic B"
    )

    initial = [s1]
    incoming = [s2, s3]
    result = merge_sources(initial, incoming)

    assert len(result) == 2
    canonical_urls = [s.canonical_url for s in result]
    assert "https://example.com/article1" in canonical_urls
    assert "https://example.com/article2" in canonical_urls


def test_research_state_structure():
    """Verify that ResearchState contains all required keys."""
    state: ResearchState = {
        "research_id": "test-123",
        "research_question": "Test topic",
        "depth": "standard",
        "max_sources": 10,
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
    assert state["research_id"] == "test-123"
    assert state["status"] == "queued"
    assert state["max_iterations"] == 2
