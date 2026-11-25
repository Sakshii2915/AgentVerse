"""Specialized Agent Status Card Component."""

import streamlit as st
from typing import Optional


AGENT_METADATA = {
    "Supervisor": {
        "icon": "🧠",
        "role": "Strategic Planning & Subtopic Decomposition",
        "description": "Formulates research subtopics, assigns priorities, and establishes investigation strategy."
    },
    "Researcher": {
        "icon": "🌐",
        "role": "Evidence Retrieval & Canonical Deduplication",
        "description": "Searches web providers, extracts page text, normalizes canonical URLs, and records metadata."
    },
    "Analyst": {
        "icon": "📊",
        "role": "Thematic Synthesis & Gap Detection",
        "description": "Synthesizes patterns, distinguishes factual evidence from projections, and identifies gaps."
    },
    "Fact Checker": {
        "icon": "🛡️",
        "role": "Claim Auditing & Contradiction Resolution",
        "description": "Cross-references factual claims against source evidence and flags contradictory assertions."
    },
    "Reviewer": {
        "icon": "⚖️",
        "role": "Quality Control & Dynamic Loop Routing",
        "description": "Evaluates research completeness and triggers targeted follow-up research cycles when needed."
    },
    "Report Generator": {
        "icon": "📄",
        "role": "Executive Synthesis & Citation Attribution",
        "description": "Publishes final structured markdown report with verified numbered citations linked to real URLs."
    }
}


def render_agent_card(
    agent_name: str,
    status: str = "pending",  # pending, running, completed, failed
    current_task: Optional[str] = None,
    summary: Optional[str] = None,
    duration: Optional[float] = None
):
    """Render a styled agent status card with telemetry details."""
    meta = AGENT_METADATA.get(agent_name, {
        "icon": "🤖",
        "role": "Specialized Agent",
        "description": "Autonomous LangGraph node."
    })

    status_lower = status.lower()
    if status_lower not in ("pending", "running", "completed", "failed"):
        status_lower = "pending"

    duration_str = f"{duration:.1f}s" if duration is not None else "—"
    task_display = current_task or meta["description"]
    summary_display = summary or "Awaiting workflow step initiation..."

    st.markdown(
        f"""
        <div class="agent-card {status_lower}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">{meta['icon']}</span>
                    <div>
                        <div style="font-weight: 600; font-size: 1.05rem; color: #f8fafc;">
                            {agent_name}
                        </div>
                        <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">
                            {meta['role']}
                        </div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-family: monospace; font-size: 0.8rem; color: #64748b;">
                        ⏱️ {duration_str}
                    </span>
                    <span class="status-pill {status_lower}">
                        {status_lower}
                    </span>
                </div>
            </div>
            <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 6px; padding: 6px 10px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                <strong style="color: #a5b4fc;">Task:</strong> {task_display}
            </div>
            <div style="font-size: 0.82rem; color: #94a3b8; margin-top: 6px; line-height: 1.4;">
                {summary_display}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
