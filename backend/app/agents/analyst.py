"""Agent 3: Analyst Agent."""

from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from app.schemas.agents import AnalystOutput, ExtractedEvidence
from app.services.llm_factory import LLMFactory
from app.utils.logging import logger

ANALYST_SYSTEM_PROMPT = """You are the Senior Intelligence Analyst in the AgentVerse multi-agent research system.
Your role is to deeply analyze the collected empirical evidence and uncover patterns, emerging trends, opportunities, and strategic risks.

CRITICAL INSTRUCTIONS:
1. Ground your analysis strictly in the provided evidence extracts.
2. Distinctly separate directly supported facts (`direct_fact`) from your analytical projections (`interpretation` or `projection`).
3. Compare findings across multiple sources to identify consensus and divergence.
4. Pinpoint remaining research gaps or unanswered angles.
5. Provide a crisp summary of evidence.
"""


class AnalystAgent:
    """Synthesizes raw evidence into structured findings, trends, and risk/opportunity vectors."""

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or LLMFactory.get_llm(temperature=0.2)

    async def analyze(
        self,
        research_question: str,
        sources: List[ExtractedEvidence]
    ) -> AnalystOutput:
        """Analyze gathered evidence and generate structured findings and trends."""
        logger.info("Analyst reviewing %d evidence sources for question: '%s'", len(sources), research_question[:60])

        # Format sources text compactly for prompt
        source_summaries = []
        for i, s in enumerate(sources[:15], 1):
            snippet = s.extracted_content[:400].replace("\n", " ")
            source_summaries.append(
                f"Source [{i}] ({s.domain}): \"{s.title}\"\n"
                f"URL: {s.url}\n"
                f"Content: {snippet}\n"
            )

        evidence_corpus = "\n".join(source_summaries) if source_summaries else "No sources available."

        human_prompt = (
            f"Original Research Question:\n{research_question}\n\n"
            f"Collected Evidence Corpus:\n{evidence_corpus}\n\n"
            "Analyze the evidence above and produce a structured analysis output identifying themes, trends, "
            "categorized findings (fact vs interpretation), opportunities, risks, and gaps."
        )

        messages = [
            SystemMessage(content=ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=human_prompt)
        ]

        structured_llm = self.llm.with_structured_output(AnalystOutput)
        analysis: AnalystOutput = await structured_llm.ainvoke(messages)
        logger.info(
            "Analyst produced %d findings, %d trends, %d gaps",
            len(analysis.findings),
            len(analysis.trends),
            len(analysis.research_gaps)
        )
        return analysis
