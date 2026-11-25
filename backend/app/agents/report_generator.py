"""Agent 5: Report Generator Agent (Final evidence synthesis & publication)."""

from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from app.schemas.agents import (
    ReportGeneratorOutput,
    AnalystOutput,
    FactCheckerOutput,
    ReviewerOutput,
    ExtractedEvidence,
    CitationItem
)
from app.services.llm_factory import LLMFactory
from app.utils.logging import logger
from app.utils.citations import CitationManager

REPORT_GENERATOR_SYSTEM_PROMPT = """You are the Senior Research Editor & Report Generator in the AgentVerse multi-agent intelligence system.
Your mission is to synthesize the verified evidence, analysis, and fact-checker audits into an executive-grade, publication-ready research report.

MANDATORY SECTIONS TO INCLUDE IN YOUR MARKDOWN REPORT:
1. `# [Report Title]`
2. `## Executive Summary` (High-impact distillation of core insights with citations)
3. `## Research Methodology` (Multi-agent decomposition, retrieval, and verification process)
4. `## Key Findings & Empirical Evidence` (Numbered sub-sections citing sources like [1], [2])
5. `## In-Depth Thematic Analysis` (Deeper analytical perspectives, trends, and implications)
6. `## Strategic Opportunities & Risk Vectors` (Bullet points for opportunities and risk vectors)
7. `## Research Limitations & Unverified Claims` (Transparent disclosure of gaps and limits)
8. `## Strategic Conclusion` (Future outlook and key recommendations)
9. `## References & Sources` (Complete numbered list matching citations [1], [2] to real URLs)

CITATION & EVIDENCE INTEGRITY RULES:
- Use in-text bracket citations [1], [2] corresponding EXACTLY to the provided source reference list.
- NEVER invent fictitious sources, fake statistics, or imaginary URLs.
- If a claim was unverified or contradictory in the fact-check audit, explicitly state this limitation.
- Distinguish between verified empirical facts and speculative interpretations.
"""


class ReportGeneratorAgent:
    """Generates comprehensive, citation-backed intelligence reports."""

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or LLMFactory.get_llm(temperature=0.2)

    async def generate(
        self,
        research_question: str,
        analyst_output: AnalystOutput,
        fact_checker_output: FactCheckerOutput,
        reviewer_output: Optional[ReviewerOutput],
        sources: List[ExtractedEvidence],
        citation_manager: CitationManager
    ) -> ReportGeneratorOutput:
        """Produce the final structured report with traceable citations."""
        logger.info("Report Generator creating final report with %d sources", len(sources))

        # Build numbered source catalog for prompt
        source_items: List[CitationItem] = []
        source_catalog_lines = []
        for s in sources:
            item = citation_manager.register_source(
                url=s.url,
                title=s.title,
                domain=s.domain,
                publication_date=s.publication_date
            )
            source_items.append(item)
            source_catalog_lines.append(
                f"[{item.number}] \"{item.title}\" | Domain: {item.domain} | URL: {item.url}"
            )

        source_catalog_str = "\n".join(source_catalog_lines) if source_catalog_lines else "No sources registered."

        # Format fact-checked findings
        claims_summary = []
        for c in fact_checker_output.claims:
            citations_str = f" Citations: {c.supporting_citation_numbers}" if c.supporting_citation_numbers else ""
            claims_summary.append(f"- [{c.verification_status.upper()}]{citations_str} {c.claim_text}")
        claims_str = "\n".join(claims_summary)

        # Reviewer feedback
        critique = reviewer_output.critique_feedback if reviewer_output else "Proceeded directly to synthesis."

        human_prompt = (
            f"Original Research Question:\n{research_question}\n\n"
            f"Verified Source Catalog (Cite these strictly by bracket numbers):\n{source_catalog_str}\n\n"
            f"Audited Claims & Verification Status:\n{claims_str}\n\n"
            f"Analyst Themes & Trends:\n{analyst_output.patterns_and_themes}\n\n"
            f"Reviewer Critique & Limitations to Disclose:\n{critique}\n\n"
            "Produce the complete structured ReportGeneratorOutput. "
            "Ensure the markdown_full_report includes all 9 required sections with proper in-text citations."
        )

        messages = [
            SystemMessage(content=REPORT_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=human_prompt)
        ]

        structured_llm = self.llm.with_structured_output(ReportGeneratorOutput)
        report: ReportGeneratorOutput = await structured_llm.ainvoke(messages)

        # Append reference section to markdown report if not already present
        if "## References" not in report.markdown_full_report and "## Sources" not in report.markdown_full_report:
            ref_md = citation_manager.build_references_markdown()
            report.markdown_full_report = f"{report.markdown_full_report.strip()}\n\n{ref_md}"

        # Ensure citations list matches registered sources
        report.citations = citation_manager.get_all_citations()

        logger.info("Report Generator completed synthesis: '%s' (%d citations)", report.title, len(report.citations))
        return report
