"""Test Researcher Agent and Search Services."""

import pytest
from app.agents.researcher import ResearcherAgent
from app.services.search_service import MockSearchProvider
from app.services.source_service import SourceService
from app.schemas.agents import SubtopicPlan
from app.utils.url_utils import normalize_canonical_url, extract_domain, is_valid_http_url


def test_url_canonical_normalization():
    url_with_tracking = "https://WWW.Example.com/article/123/?utm_source=twitter&utm_medium=social&ref=tech#overview"
    canonical = normalize_canonical_url(url_with_tracking)
    assert canonical == "https://www.example.com/article/123"
    assert "utm_source" not in canonical
    assert "#" not in canonical


def test_url_domain_extraction():
    assert extract_domain("https://www.nature.com/articles/123") == "nature.com"
    assert extract_domain("http://techcrunch.com/news") == "techcrunch.com"


def test_is_valid_http_url():
    assert is_valid_http_url("https://github.com/langchain-ai") is True
    assert is_valid_http_url("http://arxiv.org/abs/2301.0000") is True
    assert is_valid_http_url("ftp://server.example") is False
    assert is_valid_http_url("http://localhost:8000/secret") is False
    assert is_valid_http_url("http://169.254.169.254/latest") is False


@pytest.mark.asyncio
async def test_researcher_subtopic_execution(mock_search_provider):
    source_service = SourceService()
    agent = ResearcherAgent(search_provider=mock_search_provider, source_service=source_service)

    subtopic = SubtopicPlan(
        title="Developer Productivity",
        search_queries=["developer velocity ai empirical studies"],
        priority=1
    )

    evidences = await agent.execute_subtopic_research(subtopic=subtopic, max_sources_per_topic=3)
    assert len(evidences) >= 1
    for ev in evidences:
        assert ev.canonical_url != ""
        assert ev.domain != ""
        assert ev.extracted_content != ""
        assert 0.0 <= ev.relevance_score <= 1.0
