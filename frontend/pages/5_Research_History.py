"""Page 5: Research History - Mission Archive & Session Management."""

import streamlit as st
import os
import sys

# Ensure frontend root is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from api_client import api_client
from components.header import render_header

st.set_page_config(page_title="Research History — AgentVerse", page_icon="📚", layout="wide")

# Theme styling
css_path = os.path.join(parent_dir, "styles", "theme.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

render_header("Research History: Autonomous Mission Archive")

history = api_client.get_history(limit=100)

if not history:
    st.info("No research sessions recorded in database. Please launch a research mission from **1_🔬_Research_Studio**.")
    st.stop()

st.markdown(f"### 🗄️ Stored Research Missions ({len(history)})")

# Search history bar
search_q = st.text_input("Filter research topics:", placeholder="Filter by prompt keyword...")

filtered_history = [
    h for h in history
    if not search_q or search_q.lower() in h.get("research_question", "").lower()
]

for item in filtered_history:
    job_id = item["id"]
    question = item.get("research_question", "")
    status = item.get("status", "unknown").lower()
    depth = item.get("depth", "standard")
    src_count = item.get("source_count", 0)
    claim_count = item.get("claim_count", 0)
    has_rep = item.get("has_report", False)
    created_at = item.get("created_at", "")[:19].replace("T", " ")

    status_color = {
        "completed": "#10b981",
        "failed": "#f43f5e",
        "cancelled": "#f59e0b",
        "queued": "#94a3b8"
    }.get(status, "#38bdf8")

    with st.container():
        st.markdown(
            f"""
            <div class="source-card" style="margin-bottom: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 0.8rem; font-family: monospace; color: #a5b4fc;">
                        📅 {created_at} • ID: {job_id}
                    </div>
                    <span style="font-size: 0.75rem; padding: 3px 10px; border-radius: 9999px; background: rgba(255,255,255,0.05); color: {status_color}; border: 1px solid {status_color}; font-weight: 700; text-transform: uppercase;">
                        {status}
                    </span>
                </div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #f8fafc; margin: 8px 0;">
                    {question}
                </div>
                <div style="font-size: 0.82rem; color: #94a3b8; display: flex; gap: 16px;">
                    <span>📊 Depth: <strong>{depth.upper()}</strong></span>
                    <span>🌐 Sources: <strong>{src_count}</strong></span>
                    <span>🛡️ Claims: <strong>{claim_count}</strong></span>
                    <span>📄 Report: <strong>{'Available' if has_rep else 'Not Generated'}</strong></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 4])
        with btn_c1:
            if st.button("📂 Reopen Mission", key=f"reopen_{job_id}", use_container_width=True):
                st.session_state.active_research_id = job_id
                st.session_state.research_question = question
                st.success(f"Context set to `{job_id}`. Switch to **2_⚡_Live_Agent_Workspace** or **3_📄_Research_Report**.")
        with btn_c2:
            if st.button("🗑️ Delete Session", key=f"del_{job_id}", type="secondary", use_container_width=True):
                deleted = api_client.delete_history_item(job_id)
                if deleted:
                    st.success("Session deleted.")
                    if st.session_state.get("active_research_id") == job_id:
                        st.session_state.active_research_id = None
                    st.rerun()
                else:
                    st.error("Failed to delete session.")
        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 8px 0 16px 0;'>", unsafe_allow_html=True)
