"""Agent 6: Reviewer Agent (Quality assurance & dynamic routing)."""

from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from app.schemas.agents import ReviewerOutput, AnalystOutput, FactCheckerOutput, ExtractedEvidence
from app.services.llm_factory import LLMFactory
from app.utils.logging import logger

REVIEWER_SYSTEM_PROMPT = """You are the Senior Reviewer and Quality Director in the AgentVerse multi-agent research system.
Your mission is to perform uncompromising peer-review on the gathered evidence, analytical rigor, and fact-check audits.

ROUTING CRITERIA:
1. `report_generator`: Choose this if:
   - Factual claims are predominantly `supported` or `partially_supported`.
   - Coverage across key dimensions of the original research question is satisfactory.
   - Contradictions have been identified and contextualized.
2. `researcher`: Choose this if:
   - Critical factual gaps exist, or major claims are `unverified`.
   - Clear subtopics lack empirical evidence.
   - Provide explicit, targeted queries in `targeted_queries_for_researcher`.
3. `analyst`: Choose this if:
   - Raw evidence is present, but analytical interpretation is superficial or contradictory.

Provide honest completeness scores (0.0 to 1.0) and actionable critique.
"""


class ReviewerAgent:
    """Evaluates multi-agent research quality and determines dynamic workflow routing."""

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or LLMFactory.get_llm(temperature=0.1)

    async def review(
        self,
        research_question: str,
        analyst_output: AnalystOutput,
        fact_checker_output: FactCheckerOutput,
        sources: List[ExtractedEvidence],
        current_iteration: int,
        max_iterations: int
    ) -> ReviewerOutput:
        """Evaluate evidence quality and decide whether to synthesize or loop back."""
        logger.info(
            "Reviewer evaluating iteration %d/%d (sources=%d, claims=%d)",
            current_iteration,
            max_iterations,
            len(sources),
            len(fact_checker_output.claims)
        )

        # Enforce hard upper bound if max iterations reached
        if current_iteration >= max_iterations:
            logger.info("Maximum iteration limit (%d) reached. Forcing route to report_generator.", max_iterations)
            return ReviewerOutput(
                is_sufficient=True,
                route_decision="report_generator",
                completeness_score=0.80,
                citation_coverage_score=0.85,
                critique_feedback=f"Maximum revision limit ({max_iterations}) reached. Generating comprehensive report with clearly noted research limitations.",
                missing_aspects=analyst_output.research_gaps,
                targeted_queries_for_researcher=[]
            )

        # Summarize fact check status counts
        status_counts = {}
        for c in fact_checker_output.claims:
            status_counts[c.verification_status] = status_counts.get(c.verification_status, 0) + 1

        human_prompt = (
            f"Original Question:\n{research_question}\n\n"
            f"Iteration: {current_iteration} of {max_iterations}\n"
            f"Total Sources Collected: {len(sources)}\n"
            f"Fact-Checker Status Distribution: {status_counts}\n"
            f"Contradictions Detected: {fact_checker_output.contradictions_detected}\n"
            f"Research Gaps Noted: {analyst_output.research_gaps}\n\n"
            "Evaluate whether this investigation is complete and authoritative. "
            "Decide the next routing step ('report_generator', 'researcher', or 'analyst')."
        )

        messages = [
            SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
            HumanMessage(content=human_prompt)
        ]

        structured_llm = self.llm.with_structured_output(ReviewerOutput)
        review: ReviewerOutput = await structured_llm.ainvoke(messages)

        logger.info(
            "Reviewer decision: '%s' (completeness=%.2f, sufficient=%s)",
            review.route_decision,
            review.completeness_score,
            review.is_sufficient
        )
        return review
