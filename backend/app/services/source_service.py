"""Service for source deduplication, enrichment, and persistence."""

from typing import List, Dict, Set, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.models import ResearchSource
from app.schemas.agents import ExtractedEvidence
from app.services.search_service import SearchResultItem, extract_web_content
from app.utils.logging import logger
from app.utils.url_utils import normalize_canonical_url, extract_domain
from app.utils.citations import CitationManager


class SourceService:
    """Handles source deduplication, deep extraction, and database persistence."""

    def __init__(self, citation_manager: Optional[CitationManager] = None):
        self.citation_manager = citation_manager or CitationManager()
        self.seen_canonicals: Set[str] = set()

    async def process_and_deduplicate(
        self,
        raw_items: List[SearchResultItem],
        subtopic: str,
        max_sources_to_add: int = 5,
        deep_extract: bool = True
    ) -> List[ExtractedEvidence]:
        """
        Deduplicate raw search results using canonical URLs,
        enrich with full page text if necessary, and return clean ExtractedEvidence.
        """
        deduped_evidence: List[ExtractedEvidence] = []

        for item in raw_items:
            if len(deduped_evidence) >= max_sources_to_add:
                break

            canonical = normalize_canonical_url(item.url)
            if not canonical or canonical in self.seen_canonicals:
                logger.debug("Skipping duplicate or invalid source URL: %s", item.url)
                continue

            self.seen_canonicals.add(canonical)

            # Check if we should fetch deeper page content
            content = item.snippet
            if deep_extract and len(content) < 300:
                full_text = await extract_web_content(item.url, timeout_seconds=6)
                if full_text and len(full_text) > len(content):
                    content = full_text

            # Register with citation manager
            citation = self.citation_manager.register_source(
                url=item.url,
                title=item.title,
                domain=item.domain,
                publication_date=item.publication_date
            )

            evidence = ExtractedEvidence(
                url=item.url,
                canonical_url=canonical,
                title=item.title,
                domain=item.domain,
                publication_date=item.publication_date,
                extracted_content=content,
                relevance_score=item.score,
                subtopic=subtopic
            )
            deduped_evidence.append(evidence)

        return deduped_evidence

    def persist_sources(
        self,
        db: Session,
        research_id: str,
        evidences: List[ExtractedEvidence]
    ) -> List[ResearchSource]:
        """Save evidence sources to the PostgreSQL / SQLite database with citation numbers."""
        persisted_records: List[ResearchSource] = []

        for ev in evidences:
            cit_num = self.citation_manager.get_citation_number_for_url(ev.url)
            record = ResearchSource(
                research_id=research_id,
                title=ev.title,
                url=ev.url,
                canonical_url=ev.canonical_url,
                domain=ev.domain,
                publication_date=ev.publication_date,
                extracted_content=ev.extracted_content,
                relevance_score=ev.relevance_score,
                is_canonical=True,
                citation_number=cit_num
            )
            db.add(record)
            persisted_records.append(record)

        db.commit()
        for r in persisted_records:
            db.refresh(r)

        logger.info("Persisted %d unique research sources for job %s", len(persisted_records), research_id)
        return persisted_records
