"""Conditional routing logic for the LangGraph research workflow."""

from typing import Literal
from app.graph.state import ResearchState
from app.utils.logging import logger


def route_after_review(
    state: ResearchState
) -> Literal["report_generator", "researcher", "analyst"]:
    """
    Evaluates Reviewer recommendations and iteration limits to route to the next agent node.
    Enforces bounded loops to prevent endless agent cycles.
    """
    iteration = state.get("current_iteration", 0)
    max_iterations = state.get("max_iterations", 2)
    review = state.get("review")

    logger.info(
        "Routing evaluation at iteration %d/%d (review decision: %s)",
        iteration,
        max_iterations,
        review.route_decision if review else "None"
    )

    # 1. Hard bound check
    if iteration >= max_iterations:
        logger.info("Enforcing upper iteration limit (%d). Routing directly to report_generator.", max_iterations)
        return "report_generator"

    if not review:
        return "report_generator"

    # 2. Reviewer targeted routing
    if review.route_decision == "researcher":
        logger.info("Reviewer requested additional research. Routing back to researcher node.")
        return "researcher"

    if review.route_decision == "analyst":
        logger.info("Reviewer requested deeper analysis. Routing back to analyst node.")
        return "analyst"

    logger.info("Reviewer approved evidence sufficiency. Routing to report_generator node.")
    return "report_generator"
