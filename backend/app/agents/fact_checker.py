"""Agent 4: Fact-Checker Agent."""

from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from app.schemas.agents import FactCheckerOutput, AnalystOutput, ExtractedEvidence
from app.services.llm_factory import LLMFactory
from app.utils.logging import logger

FACT_CHECKER_SYSTEM_PROMPT = """You are the Senior Fact-Checker and Evidence Verifier in the AgentVerse multi-agent research system.
Your mission is to rigorously audit key factual assertions against the gathered evidence corpus.

CRITICAL RULES:
1. Examine each major claim extracted from the research analysis.
2. Cross-reference every claim against the provided sources by source index (e.g., [1], [2]).
3. Classify each claim strictly as:
   - `supported`: The text of cited sources explicitly corroborates the statement.
   - `partially_supported`: Evidence provides partial backing but lacks specific metrics or scope.
   - `contradicted`: Source evidence directly refutes, conflicts with, or invalidates the claim.
   - `unverified`: The claim is not addressed by any of the available sources.
4. When a claim is contradicted, document the exact conflicting evidence.
5. If major factual gaps exist or key claims are unverified/contradicted, set `additional_research_needed=True` and suggest specific queries.
6. NEVER fabricate citations or assume truth without source textual evidence.
"""


class FactCheckerAgent:
    """Verifies factual claims against source evidence corpus."""

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or LLMFactory.get_llm(temperature=0.1)

    async def verify(
        self,
        research_question: str,
        analyst_output: AnalystOutput,
        sources: List[ExtractedEvidence]
    ) -> FactCheckerOutput:
        """Verify analyst findings and claims against source corpus."""
        logger.info("Fact-Checker auditing claims against %d sources", len(sources))

        # Format sources text with citation indices
        source_texts = []
        for idx, s in enumerate(sources, 1):
            source_texts.append(
                f"[{idx}] Title: {s.title} ({s.domain})\n"
                f"URL: {s.url}\n"
                f"Content Extract: {s.extracted_content[:350]}\n"
            )
        corpus_str = "\n".join(source_texts) if source_texts else "No sources available."

        # Format statements to verify from analyst
        statements_to_check = []
        for f in analyst_output.findings:
            statements_to_check.append(f"- ({f.evidence_type}): {f.statement}")
        for t in analyst_output.trends:
            statements_to_check.append(f"- (trend): {t.trend_name} - {t.description}")
        claims_str = "\n".join(statements_to_check)

        human_prompt = (
            f"Research Question:\n{research_question}\n\n"
            f"Source Evidence Corpus:\n{corpus_str}\n\n"
            f"Claims and Findings to Audit:\n{claims_str}\n\n"
            "Audit each assertion. Return verified claims with status ('supported', 'partially_supported', "
            "'contradicted', 'unverified'), citation indices, confidence scores, and identify any contradictions."
        )

        messages = [
            SystemMessage(content=FACT_CHECKER_SYSTEM_PROMPT),
            HumanMessage(content=human_prompt)
        ]

        structured_llm = self.llm.with_structured_output(FactCheckerOutput)
        result: FactCheckerOutput = await structured_llm.ainvoke(messages)

        logger.info(
            "Fact-Checker verified %d claims (credibility score: %.2f, contradictions: %d)",
            len(result.claims),
            result.overall_credibility_score,
            len(result.contradictions_detected)
        )
        return result
