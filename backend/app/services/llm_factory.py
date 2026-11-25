"""LLM Factory providing ChatOpenAI or intelligent mock LLM for testing/demo mode."""

import json
from typing import Any, Optional, Type, Dict
from pydantic import BaseModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage

from app.config import settings
from app.utils.logging import logger


class StructuredMockRunnable:
    """Fast, deterministic runnable supporting both invoke and ainvoke for MockLLM."""

    def __init__(self, schema: Type[BaseModel]):
        self.schema = schema

    def invoke(self, inputs: Any, **kwargs: Any):
        return self._generate(inputs)

    async def ainvoke(self, inputs: Any, **kwargs: Any):
        return self._generate(inputs)

    def _generate(self, inputs: Any):
        schema_name = self.schema.__name__
        logger.info("MockLLM producing structured schema: %s", schema_name)

        if schema_name == "SupervisorPlanOutput":
            from app.schemas.agents import SupervisorPlanOutput, SubtopicPlan
            query_str = "generative AI on software engineering"
            if isinstance(inputs, list):
                for m in inputs:
                    if hasattr(m, "content") and len(str(m.content)) > 10:
                        query_str = str(m.content)
                        break
            elif isinstance(inputs, str):
                query_str = inputs

            return SupervisorPlanOutput(
                domain="Computer Science & Technology Economics",
                objective_summary=f"Investigate: {query_str[:100]}",
                subtopics=[
                    SubtopicPlan(
                        title="Impact on Developer Productivity and Code Generation",
                        search_queries=[
                            "generative AI developer productivity statistics github copilot",
                            "AI code generation empirical benchmark studies 2024"
                        ],
                        priority=1,
                        target_aspects=["Velocity changes", "Code quality metrics"]
                    ),
                    SubtopicPlan(
                        title="Shifts in Engineering Skill Requirements and Junior Roles",
                        search_queries=[
                            "generative AI software engineer hiring junior developer demand",
                            "software engineering workforce transition prompt engineering architectural skills"
                        ],
                        priority=2,
                        target_aspects=["Junior vs senior hiring", "Skill shifts"]
                    ),
                    SubtopicPlan(
                        title="Software Architecture, Maintenance and Technical Debt",
                        search_queries=[
                            "AI generated code maintenance technical debt security vulnerabilities",
                            "long term impact generative AI software maintainability"
                        ],
                        priority=3,
                        target_aspects=["Code security", "Technical debt accumulation"]
                    )
                ],
                strategic_rationale="Deconstructs the question across immediate productivity, workforce career trajectories, and long-term codebase health."
            )

        elif schema_name == "AnalystOutput":
            from app.schemas.agents import AnalystOutput, AnalystFinding, AnalystTrend
            return AnalystOutput(
                patterns_and_themes=[
                    "Significant acceleration in repetitive boilerplate coding",
                    "Elevated emphasis on testing, validation, and architectural oversight",
                    "Heightened scrutiny on software security and license compliance"
                ],
                trends=[
                    AnalystTrend(
                        trend_name="Task Automation vs Job Elimination",
                        description="AI tools automate individual coding tasks rather than replacing complete engineering roles.",
                        evidence_basis="Multiple industry surveys indicate developers spend ~20-30% more time on design and review."
                    ),
                    AnalystTrend(
                        trend_name="Bifurcation of Engineering Skillsets",
                        description="Demand is polarizing toward high-level system architects and AI-fluent specialists.",
                        evidence_basis="Job market data shows resilient demand for senior systems engineers."
                    )
                ],
                findings=[
                    AnalystFinding(
                        statement="Studies report 20% to 55% task completion speedups for standardized programming tasks.",
                        evidence_type="direct_fact",
                        supporting_urls=[]
                    ),
                    AnalystFinding(
                        statement="Long-term code churn and technical debt may increase without automated verification guardrails.",
                        evidence_type="interpretation",
                        supporting_urls=[]
                    )
                ],
                opportunities=[
                    "Faster prototype validation and product iteration cycles",
                    "Lower barrier to entry for cross-disciplinary domain software development"
                ],
                risks_and_challenges=[
                    "Potential deskilling of early-career engineers in foundational debugging",
                    "Security vulnerabilities inadvertently introduced by hallucinated dependencies"
                ],
                research_gaps=[
                    "Longitudinal five-year empirical data on enterprise software lifecycle costs"
                ],
                summary_of_evidence="Evidence demonstrates clear productivity gains balanced by growing concerns over code maintainability."
            )

        elif schema_name == "FactCheckerOutput":
            from app.schemas.agents import FactCheckerOutput, VerifiedClaim
            return FactCheckerOutput(
                claims=[
                    VerifiedClaim(
                        claim_text="Developer productivity increases by 20% to 55% during routine coding tasks using AI assistance.",
                        verification_status="supported",
                        supporting_citation_numbers=[1],
                        supporting_urls=[],
                        confidence=0.92,
                        reasoning="Directly confirmed by empirical field experiments and multiple developer telemetry reports.",
                        contradictory_evidence=None
                    ),
                    VerifiedClaim(
                        claim_text="Software engineering employment will completely decline over the next 5 years.",
                        verification_status="contradicted",
                        supporting_citation_numbers=[],
                        supporting_urls=[],
                        confidence=0.88,
                        reasoning="Labor statistics and corporate hiring roadmaps indicate headcount growth redirected to higher-level architecture.",
                        contradictory_evidence="BLS and Gartner project ongoing demand for software engineers with evolved skills."
                    ),
                    VerifiedClaim(
                        claim_text="AI assistants introduce subtle logic and security flaws requiring expert human review.",
                        verification_status="supported",
                        supporting_citation_numbers=[2],
                        supporting_urls=[],
                        confidence=0.89,
                        reasoning="Static code analysis benchmarks demonstrate vulnerabilities in unsanitized generated code.",
                        contradictory_evidence=None
                    )
                ],
                overall_credibility_score=0.90,
                unsupported_claims_summary=[],
                contradictions_detected=[
                    "Contradicted claim that software engineering jobs will be eliminated within 5 years."
                ],
                additional_research_needed=False,
                recommended_queries=[]
            )

        elif schema_name == "ReviewerOutput":
            from app.schemas.agents import ReviewerOutput
            return ReviewerOutput(
                is_sufficient=True,
                route_decision="report_generator",
                completeness_score=0.88,
                citation_coverage_score=0.90,
                critique_feedback="Research evidence is robust across productivity, employment trends, and code quality. Ready for final synthesis.",
                missing_aspects=[],
                targeted_queries_for_researcher=[]
            )

        elif schema_name == "ReportGeneratorOutput":
            from app.schemas.agents import ReportGeneratorOutput, CitationItem
            md_report = (
                "# Impact of Generative AI on Software Engineering Jobs (2025–2030)\n\n"
                "## Executive Summary\n"
                "Generative AI is reshaping the software engineering profession through substantial productivity enhancement rather than widespread role elimination [1]. Over the next five years, developer workflows will undergo fundamental transformation, shifting engineering focus from syntactic code composition to systems architecture, automated verification, and prompt orchestration [2].\n\n"
                "## Research Methodology\n"
                "A multi-agent autonomous workflow gathered empirical studies, industry benchmark data, and labor projections. Collected evidence was deduplicated, cross-verified, and evaluated for contradictions before synthesis.\n\n"
                "## Key Findings and Detailed Analysis\n\n"
                "### 1. Developer Productivity Dynamics\n"
                "Empirical investigations confirm 20% to 55% speedups in routine programming and boilerplate generation [1]. However, gains vary significantly across development phases, with architecture and debugging continuing to demand deep human cognitive insight.\n\n"
                "### 2. Evolution of Junior vs Senior Roles\n"
                "Entry-level roles face rising expectations, as basic syntax generation is automated. High-leverage skills such as prompt system design, rigorous code review, and cybersecurity compliance have grown in priority [2].\n\n"
                "## Risks and Opportunities\n"
                "- **Opportunities**: Dramatic acceleration of software shipping cadence; democratization of custom internal tooling.\n"
                "- **Risks**: Increased code churn and hidden security vulnerabilities if generated code is merged without thorough validation.\n\n"
                "## Limitations\n"
                "Quantitative five-year forecasts remain subject to macroeconomic fluctuations and rapid model capability upgrades.\n\n"
                "## Conclusion\n"
                "Software engineering will remain vital, but the nature of the craft is evolving decisively into higher-abstraction system leadership.\n"
            )
            return ReportGeneratorOutput(
                title="Impact of Generative AI on Software Engineering Jobs (2025–2030)",
                executive_summary=(
                    "Generative AI is driving a profound shift in software engineering: rather than eliminating roles, "
                    "it automates routine implementation while elevating the value of architectural judgment, security audit, and system design."
                ),
                methodology="Multi-agent evidence retrieval, canonical deduplication, claim verification, and structured synthesis.",
                key_findings=[
                    "Routine coding tasks experience 20-55% speed improvements under AI assistance [1].",
                    "Role elimination fears are contradicted by projections showing demand redirected to complex systems engineering [2].",
                    "Unchecked AI code output poses risks of elevated technical debt and subtle security flaws."
                ],
                detailed_analysis="Extensive synthesis across developer telemetry, workforce dynamics, and software maintainability metrics.",
                risks_and_opportunities={
                    "opportunities": [
                        "Accelerated time-to-market for enterprise applications",
                        "Reduced overhead on repetitive boilerplate documentation and test scaffold creation"
                    ],
                    "risks": [
                        "Potential security debt and unverified third-party package dependencies",
                        "Erosion of foundational algorithmic intuition among early-career engineers"
                    ]
                },
                limitations="Longitudinal data on maintenance cost of AI-generated enterprise codebases remains in early stages.",
                conclusion="Software engineering is not dying; it is ascending to a higher level of architectural abstraction.",
                markdown_full_report=md_report,
                citations=[
                    CitationItem(
                        number=1,
                        title="Empirical Assessment of AI Code Generation on Developer Velocity",
                        url="https://research.example.org/analysis/101",
                        domain="research.example.org",
                        publication_date="2024-10-15"
                    ),
                    CitationItem(
                        number=2,
                        title="Workforce Trends and Skill Transitions in Modern Software Engineering",
                        url="https://journal.acm.example.edu/articles/202",
                        domain="journal.acm.example.edu",
                        publication_date="2024-08-20"
                    )
                ]
            )

        return self.schema()


class MockLLM(BaseChatModel):
    """
    Deterministic mock chat model that supports structured outputs and standard invokes
    for automated tests and environments without configured OpenAI API keys.
    """
    model_name: str = "mock-agent-llm"

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _generate(self, messages: list[BaseMessage], stop: Optional[list[str]] = None, **kwargs: Any):
        last_text = messages[-1].content if messages else ""
        return AIMessage(content=f"Mock response for: {last_text[:50]}")

    async def _agenerate(self, messages: list[BaseMessage], stop: Optional[list[str]] = None, **kwargs: Any):
        return self._generate(messages, stop, **kwargs)

    def with_structured_output(self, schema: Type[BaseModel], **kwargs: Any):
        """Return a runnable wrapper that produces valid instances of schema."""
        return StructuredMockRunnable(schema=schema)


class LLMFactory:
    """Factory to acquire ChatOpenAI or MockLLM depending on environment."""

    @staticmethod
    def get_llm(model: Optional[str] = None, temperature: Optional[float] = None) -> BaseChatModel:
        if settings.is_openai_configured:
            from langchain_openai import ChatOpenAI
            logger.info("Initializing ChatOpenAI model: %s", model or settings.OPENAI_MODEL)
            return ChatOpenAI(
                model=model or settings.OPENAI_MODEL,
                temperature=temperature if temperature is not None else settings.OPENAI_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.REQUEST_TIMEOUT
            )
        else:
            logger.info("OpenAI API key not configured. Using intelligent MockLLM.")
            return MockLLM()
