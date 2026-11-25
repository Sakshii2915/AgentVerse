"""Citation management, numbering, and source traceability utilities."""

import re
from typing import List, Dict, Any, Optional
from app.schemas.agents import CitationItem


class CitationManager:
    """Manages sequential citation numbers and formats verifiable references."""

    def __init__(self):
        self._sources_by_url: Dict[str, CitationItem] = {}
        self._sources_by_number: Dict[int, CitationItem] = {}
        self._counter: int = 1

    def register_source(
        self,
        url: str,
        title: str,
        domain: str,
        publication_date: Optional[str] = None
    ) -> CitationItem:
        """Register a source and return its assigned CitationItem with a stable citation number."""
        from app.utils.url_utils import normalize_canonical_url
        canonical = normalize_canonical_url(url)

        if canonical in self._sources_by_url:
            return self._sources_by_url[canonical]

        item = CitationItem(
            number=self._counter,
            title=title.strip() if title else "Untitled Source",
            url=url,
            domain=domain,
            publication_date=publication_date
        )
        self._sources_by_url[canonical] = item
        self._sources_by_number[self._counter] = item
        self._counter += 1
        return item

    def get_citation_by_number(self, number: int) -> Optional[CitationItem]:
        """Retrieve citation by index."""
        return self._sources_by_number.get(number)

    def get_citation_number_for_url(self, url: str) -> Optional[int]:
        """Lookup citation number for URL."""
        from app.utils.url_utils import normalize_canonical_url
        canonical = normalize_canonical_url(url)
        item = self._sources_by_url.get(canonical)
        return item.number if item else None

    def get_all_citations(self) -> List[CitationItem]:
        """Return citations sorted by citation number."""
        return sorted(self._sources_by_number.values(), key=lambda x: x.number)

    def build_references_markdown(self) -> str:
        """Format the full references list in Markdown."""
        if not self._sources_by_number:
            return "*No external sources recorded.*"

        lines = ["## References & Sources\n"]
        for item in self.get_all_citations():
            date_str = f" ({item.publication_date})" if item.publication_date else ""
            lines.append(
                f"[{item.number}] **{item.title}**{date_str}. *{item.domain}*.  \n"
                f"    [Direct Link]({item.url})\n"
            )
        return "\n".join(lines)


def extract_in_text_citations(text: str) -> List[int]:
    """Find all citation numbers referenced in brackets like [1], [2], [1, 3]."""
    matches = re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", text)
    cited_numbers = set()
    for match in matches:
        parts = match.split(",")
        for p in parts:
            p_strip = p.strip()
            if p_strip.isdigit():
                cited_numbers.add(int(p_strip))
    return sorted(list(cited_numbers))


def calculate_citation_coverage(text: str, total_sources: int) -> float:
    """Calculate the ratio of available sources cited in text."""
    if total_sources == 0:
        return 0.0
    cited = extract_in_text_citations(text)
    # Valid cited numbers within range [1..total_sources]
    valid_cited = [n for n in cited if 1 <= n <= total_sources]
    return min(1.0, len(valid_cited) / float(total_sources))
