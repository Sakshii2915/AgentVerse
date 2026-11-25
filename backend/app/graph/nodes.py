"""Execution nodes for the LangGraph multi-agent research workflow."""

import time
from datetime import datetime
from typing import Dict, Any, List

from app.graph.state import ResearchState
from app.agents.supervisor import SupervisorAgent
from app.agents.researcher import ResearcherAgent
from app.agents.analyst import AnalystAgent
from app.agents.fact_checker import FactCheckerAgent
from app.agents.report_generator import ReportGeneratorAgent
from app.agents.reviewer import ReviewerAgent
from app.utils.citations import CitationManager
from app.utils.logging import logger


async def supervisor_node(state: ResearchState) -> Dict[str, Any]:
    """Node 1: Supervisor / Planner Agent."""
    start_time = time.time()
    research_id = state["research_id"]
    question = state["research_question"]
    depth = state.get("depth", "standard")

    logger.info("[Workflow] Node 'supervisor' started for job %s", research_id)
    agent = SupervisorAgent()

    try:
        plan = await agent.plan(research_question=question, depth=depth)
        duration = round(time.time() - start_time, 2)
        log_entry = {
            "agent_name": "Supervisor",
            "status": "completed",
            "execution_time": duration,
            "input_summary": f"Question: {question[:100]} | Depth: {depth}",
            "output_summary": f"Identified domain '{plan.domain}' and created {len(plan.subtopics)} subtopic tasks.",
            "error_message": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Supervisor",
            "status": "planning",
            "plan": plan,
            "agent_logs": [log_entry]
        }
    except Exception as exc:
        duration = round(time.time() - start_time, 2)
        logger.error("[Workflow] Supervisor failed: %s", exc)
        log_entry = {
            "agent_name": "Supervisor",
            "status": "failed",
            "execution_time": duration,
            "input_summary": question[:100],
            "output_summary": "",
            "error_message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Supervisor",
            "status": "failed",
            "error": str(exc),
            "agent_logs": [log_entry]
        }


async def researcher_node(state: ResearchState) -> Dict[str, Any]:
    """Node 2: Researcher Agent."""
    start_time = time.time()
    research_id = state["research_id"]
    plan = state.get("plan")
    review = state.get("review")
    existing_sources = state.get("sources", [])
    max_sources = state.get("max_sources", 10)

    logger.info("[Workflow] Node 'researcher' started for job %s (existing sources: %d)", research_id, len(existing_sources))
    agent = ResearcherAgent()

    try:
        new_evidence = []
        # Check if running a targeted revision loop
        if review and review.targeted_queries_for_researcher:
            logger.info("Researcher executing targeted queries requested by reviewer: %s", review.targeted_queries_for_researcher)
            targeted_results = await agent.execute_targeted_research(
                queries=review.targeted_queries_for_researcher,
                max_sources=4
            )
            new_evidence.extend(targeted_results)
        elif plan and plan.subtopics:
            # Initial multi-subtopic research
            sources_per_topic = max(2, max_sources // len(plan.subtopics))
            for subtopic in plan.subtopics:
                sub_evidence = await agent.execute_subtopic_research(
                    subtopic=subtopic,
                    max_sources_per_topic=sources_per_topic
                )
                new_evidence.extend(sub_evidence)

        duration = round(time.time() - start_time, 2)
        log_entry = {
            "agent_name": "Researcher",
            "status": "completed",
            "execution_time": duration,
            "input_summary": f"Investigated {len(plan.subtopics) if plan else 0} subtopics / targeted queries.",
            "output_summary": f"Retrieved and deduplicated {len(new_evidence)} verified evidence sources.",
            "error_message": None,
            "timestamp": datetime.utcnow().isoformat()
        }

        return {
            "current_agent": "Researcher",
            "status": "researching",
            "sources": new_evidence,
            "agent_logs": [log_entry]
        }
    except Exception as exc:
        duration = round(time.time() - start_time, 2)
        logger.error("[Workflow] Researcher failed: %s", exc)
        log_entry = {
            "agent_name": "Researcher",
            "status": "failed",
            "execution_time": duration,
            "input_summary": "Web search and extraction",
            "output_summary": "",
            "error_message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Researcher",
            "status": "failed",
            "error": str(exc),
            "agent_logs": [log_entry]
        }


async def analyst_node(state: ResearchState) -> Dict[str, Any]:
    """Node 3: Analyst Agent."""
    start_time = time.time()
    research_id = state["research_id"]
    question = state["research_question"]
    sources = state.get("sources", [])

    logger.info("[Workflow] Node 'analyst' started for job %s with %d sources", research_id, len(sources))
    agent = AnalystAgent()

    try:
        analysis = await agent.analyze(research_question=question, sources=sources)
        duration = round(time.time() - start_time, 2)
        log_entry = {
            "agent_name": "Analyst",
            "status": "completed",
            "execution_time": duration,
            "input_summary": f"Analyzed {len(sources)} sources for evidence patterns.",
            "output_summary": f"Extracted {len(analysis.findings)} findings, {len(analysis.trends)} trends, and identified {len(analysis.research_gaps)} research gaps.",
            "error_message": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Analyst",
            "status": "analyzing",
            "analysis": analysis,
            "agent_logs": [log_entry]
        }
    except Exception as exc:
        duration = round(time.time() - start_time, 2)
        logger.error("[Workflow] Analyst failed: %s", exc)
        log_entry = {
            "agent_name": "Analyst",
            "status": "failed",
            "execution_time": duration,
            "input_summary": f"Evidence corpus ({len(sources)} sources)",
            "output_summary": "",
            "error_message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Analyst",
            "status": "failed",
            "error": str(exc),
            "agent_logs": [log_entry]
        }


async def fact_checker_node(state: ResearchState) -> Dict[str, Any]:
    """Node 4: Fact-Checker Agent."""
    start_time = time.time()
    research_id = state["research_id"]
    question = state["research_question"]
    analysis = state.get("analysis")
    sources = state.get("sources", [])

    logger.info("[Workflow] Node 'fact_checker' started for job %s", research_id)
    agent = FactCheckerAgent()

    try:
        fact_check = await agent.verify(
            research_question=question,
            analyst_output=analysis,
            sources=sources
        )
        duration = round(time.time() - start_time, 2)
        supported_count = sum(1 for c in fact_check.claims if c.verification_status == "supported")
        contradicted_count = sum(1 for c in fact_check.claims if c.verification_status == "contradicted")
        log_entry = {
            "agent_name": "Fact Checker",
            "status": "completed",
            "execution_time": duration,
            "input_summary": f"Audited claims across {len(sources)} sources.",
            "output_summary": f"Audited {len(fact_check.claims)} claims ({supported_count} supported, {contradicted_count} contradicted). Credibility: {int(fact_check.overall_credibility_score * 100)}%.",
            "error_message": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Fact Checker",
            "status": "fact_checking",
            "fact_check": fact_check,
            "agent_logs": [log_entry]
        }
    except Exception as exc:
        duration = round(time.time() - start_time, 2)
        logger.error("[Workflow] Fact-Checker failed: %s", exc)
        log_entry = {
            "agent_name": "Fact Checker",
            "status": "failed",
            "execution_time": duration,
            "input_summary": "Claims verification",
            "output_summary": "",
            "error_message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Fact Checker",
            "status": "failed",
            "error": str(exc),
            "agent_logs": [log_entry]
        }


async def reviewer_node(state: ResearchState) -> Dict[str, Any]:
    """Node 5: Reviewer Agent."""
    start_time = time.time()
    research_id = state["research_id"]
    question = state["research_question"]
    analysis = state.get("analysis")
    fact_check = state.get("fact_check")
    sources = state.get("sources", [])
    current_iter = state.get("current_iteration", 0)
    max_iters = state.get("max_iterations", 2)

    logger.info("[Workflow] Node 'reviewer' started for job %s (iteration %d/%d)", research_id, current_iter, max_iters)
    agent = ReviewerAgent()

    try:
        review = await agent.review(
            research_question=question,
            analyst_output=analysis,
            fact_checker_output=fact_check,
            sources=sources,
            current_iteration=current_iter,
            max_iterations=max_iters
        )
        duration = round(time.time() - start_time, 2)
        next_iter = current_iter + 1
        log_entry = {
            "agent_name": "Reviewer",
            "status": "completed",
            "execution_time": duration,
            "input_summary": f"Evaluated completeness at iteration {current_iter}.",
            "output_summary": f"Decision: '{review.route_decision}' (completeness: {int(review.completeness_score * 100)}%). Feedback: {review.critique_feedback[:80]}...",
            "error_message": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Reviewer",
            "status": "reviewing",
            "review": review,
            "current_iteration": next_iter,
            "agent_logs": [log_entry]
        }
    except Exception as exc:
        duration = round(time.time() - start_time, 2)
        logger.error("[Workflow] Reviewer failed: %s", exc)
        log_entry = {
            "agent_name": "Reviewer",
            "status": "failed",
            "execution_time": duration,
            "input_summary": "Quality evaluation",
            "output_summary": "",
            "error_message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Reviewer",
            "status": "failed",
            "error": str(exc),
            "current_iteration": current_iter + 1,
            "agent_logs": [log_entry]
        }


async def report_generator_node(state: ResearchState) -> Dict[str, Any]:
    """Node 6: Report Generator Agent."""
    start_time = time.time()
    research_id = state["research_id"]
    question = state["research_question"]
    analysis = state.get("analysis")
    fact_check = state.get("fact_check")
    review = state.get("review")
    sources = state.get("sources", [])

    logger.info("[Workflow] Node 'report_generator' started for job %s", research_id)
    agent = ReportGeneratorAgent()
    citation_manager = CitationManager()

    try:
        report = await agent.generate(
            research_question=question,
            analyst_output=analysis,
            fact_checker_output=fact_check,
            reviewer_output=review,
            sources=sources,
            citation_manager=citation_manager
        )
        duration = round(time.time() - start_time, 2)
        log_entry = {
            "agent_name": "Report Generator",
            "status": "completed",
            "execution_time": duration,
            "input_summary": f"Synthesized findings with {len(report.citations)} citations.",
            "output_summary": f"Published '{report.title}' with {len(report.key_findings)} core findings and {len(report.citations)} verified references.",
            "error_message": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Report Generator",
            "status": "completed",
            "report": report,
            "agent_logs": [log_entry]
        }
    except Exception as exc:
        duration = round(time.time() - start_time, 2)
        logger.error("[Workflow] Report Generator failed: %s", exc)
        log_entry = {
            "agent_name": "Report Generator",
            "status": "failed",
            "execution_time": duration,
            "input_summary": "Report synthesis",
            "output_summary": "",
            "error_message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "current_agent": "Report Generator",
            "status": "failed",
            "error": str(exc),
            "agent_logs": [log_entry]
        }
