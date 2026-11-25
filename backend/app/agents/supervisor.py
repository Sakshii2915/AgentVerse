"""Agent 1: Supervisor / Planner Agent."""

from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from app.schemas.agents import SupervisorPlanOutput
from app.services.llm_factory import LLMFactory
from app.utils.logging import logger

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor and Chief Research Planner in the AgentVerse multi-agent system.
Your mission is to rigorously analyze the user's research question, understand its core domain, and decompose it into 3 to 6 highly targeted research subtopics.

Guidelines:
1. Identify the academic, technical, or industrial domain.
2. Break the central question into 3 to 6 distinct, non-overlapping subtopics.
3. For each subtopic, provide 2 to 3 high-precision search queries suitable for web search engines.
4. Assign strict priority (1 = critical foundational evidence, 2 = deep dive/trends, 3 = risks/future projections).
5. Never hallucinate search results here; only plan the research architecture.
"""


class SupervisorAgent:
    """Orchestrates research strategy and task decomposition."""

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or LLMFactory.get_llm(temperature=0.1)

    async def plan(self, research_question: str, depth: str = "standard") -> SupervisorPlanOutput:
        """Analyze research question and produce a structured investigation plan."""
        logger.info("Supervisor planning research for question: '%s' (depth=%s)", research_question[:60], depth)

        human_prompt = (
            f"User Research Objective:\n{research_question}\n\n"
            f"Configured Depth: {depth}\n"
            "Produce a structured research plan decomposing this topic into 3-6 focused subtopics with targeted queries."
        )

        messages = [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=human_prompt)
        ]

        structured_llm = self.llm.with_structured_output(SupervisorPlanOutput)
        plan: SupervisorPlanOutput = await structured_llm.ainvoke(messages)
        logger.info("Supervisor generated %d subtopics across domain: '%s'", len(plan.subtopics), plan.domain)
        return plan
