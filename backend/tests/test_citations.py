"""Test Citation Management and Source Traceability."""

import pytest
from app.utils.citations import CitationManager, extract_in_text_citations, calculate_citation_coverage


def test_citation_manager_registration():
    cm = CitationManager()
    item1 = cm.register_source(
        url="https://nature.com/articles/101?utm_source=twitter",
        title="AI Benchmarks",
        domain="nature.com",
        publication_date="2024-05-12"
    )
    assert item1.number == 1
    assert item1.domain == "nature.com"

    # Register same URL (with different query param) -> should return same citation item
    item1_dup = cm.register_source(
        url="https://nature.com/articles/101?fbclid=abc",
        title="AI Benchmarks Dup",
        domain="nature.com"
    )
    assert item1_dup.number == 1

    # Register second URL
    item2 = cm.register_source(
        url="https://ieee.org/papers/202",
        title="Software Engineering 2025",
        domain="ieee.org"
    )
    assert item2.number == 2

    assert len(cm.get_all_citations()) == 2
    md_refs = cm.build_references_markdown()
    assert "[1] **AI Benchmarks**" in md_refs
    assert "[2] **Software Engineering 2025**" in md_refs


def test_extract_in_text_citations():
    text = (
        "According to empirical studies [1], developer speed increased by 35%. "
        "Furthermore, security audits [2, 3] identified new vulnerabilities."
    )
    citations = extract_in_text_citations(text)
    assert citations == [1, 2, 3]


def test_calculate_citation_coverage():
    text = "Key findings indicate speedup [1] and workforce shift [2]."
    coverage = calculate_citation_coverage(text, total_sources=4)
    assert coverage == 0.5  # 2 of 4 sources cited

    text_all = "Finding [1], finding [2], finding [3], finding [4]."
    assert calculate_citation_coverage(text_all, total_sources=4) == 1.0
