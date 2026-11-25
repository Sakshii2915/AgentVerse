"""Agent 2: Researcher Agent."""

from typing import List, Optional, Set
from app.schemas.agents import SubtopicPlan, ExtractedEvidence, ResearcherBatchOutput
from app.services.search_service import BaseSearchProvider, SearchProviderFactory, SearchResultItem
from app.services.source_service import SourceService
from app.utils.logging import logger
from app.utils.url_utils import normalize_canonical_url, extract_domain


class ResearcherAgent:
    """Performs targeted web search, deduplication, and evidence extraction."""

    def __init__(
        self,
        search_provider: Optional[BaseSearchProvider] = None,
        source_service: Optional[SourceService] = None
    ):
        self.search_provider = search_provider or SearchProviderFactory.get_provider()
        self.source_service = source_service or SourceService()

    async def execute_subtopic_research(
        self,
        subtopic: SubtopicPlan,
        max_sources_per_topic: int = 4
    ) -> List[ExtractedEvidence]:
        """Search the web for a specific subtopic's queries and extract verified evidence."""
        logger.info("Researcher investigating subtopic: '%s'", subtopic.title)
        all_raw_results: List[SearchResultItem] = []

        for query in subtopic.search_queries:
            results = await self.search_provider.search(query=query, max_results=max_sources_per_topic)
            all_raw_results.extend(results)

        # Process and deduplicate against global seen URLs
        evidences = await self.source_service.process_and_deduplicate(
            raw_items=all_raw_results,
            subtopic=subtopic.title,
            max_sources_to_add=max_sources_per_topic,
            deep_extract=True
        )

        logger.info("Researcher obtained %d unique evidence sources for '%s'", len(evidences), subtopic.title)
        return evidences

    async def execute_targeted_research(
        self,
        queries: List[str],
        max_sources: int = 4
    ) -> List[ExtractedEvidence]:
        """Execute specific targeted queries triggered during review revision cycles."""
        logger.info("Researcher running targeted follow-up queries: %s", queries)
        all_raw_results: List[SearchResultItem] = []

        for q in queries:
            results = await self.search_provider.search(query=q, max_results=3)
            all_raw_results.extend(results)

        evidences = await self.source_service.process_and_deduplicate(
            raw_items=all_raw_results,
            subtopic="Targeted Follow-up Investigation",
            max_sources_to_add=max_sources,
            deep_extract=True
        )

        return evidences
