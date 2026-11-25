"""Page 2: Live Agent Workspace - Real-time Multi-Agent Telemetry & Orchestration."""

import streamlit as st
import time
import os
import sys

# Ensure frontend root is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from api_client import api_client
from components.header import render_header
from components.agent_card import render_agent_card

st.set_page_config(page_title="Live Agent Workspace — AgentVerse", page_icon="⚡", layout="wide")

# Theme styling
css_path = os.path.join(parent_dir, "styles", "theme.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

render_header("Live Workspace: Real-Time Multi-Agent Orchestration")

# Select active research job
active_id = st.session_state.get("active_research_id")

# Dropdown to switch or pick past jobs
history = api_client.get_history(limit=20)
job_options = {h["id"]: f"{h['research_question'][:60]}... ({h['status'].upper()})" for h in history}

if not job_options and not active_id:
    st.info("No active research missions found. Please visit **1_🔬_Research_Studio** to launch a new mission.")
    st.stop()

# Header controls
top_col1, top_col2, top_col3 = st.columns([3, 1, 1])

with top_col1:
    selected_id = st.selectbox(
        "Current Mission Context:",
        options=list(job_options.keys()),
        index=list(job_options.keys()).index(active_id) if active_id in job_options else 0,
        format_func=lambda x: job_options.get(x, x)
    )
    if selected_id != active_id:
        st.session_state.active_research_id = selected_id
        active_id = selected_id

with top_col2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh State", use_container_width=True):
        st.rerun()

with top_col3:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("🛑 Cancel Mission", type="secondary", use_container_width=True):
        if active_id:
            api_client.cancel_research(active_id)
            st.warning("Cancellation request dispatched to backend.")
            st.rerun()

# Fetch live job status and telemetry from backend
job_data = api_client.get_history_detail(active_id)
if not job_data:
    st.error(f"Could not retrieve details for job '{active_id}'.")
    st.stop()

status = job_data.get("status", "unknown").lower()
question = job_data.get("research_question", "")
tasks = job_data.get("tasks", [])
sources = job_data.get("sources", [])
claims = job_data.get("claims", [])
logs = job_data.get("logs", [])
iteration = job_data.get("current_iteration", 0)
max_iter = job_data.get("max_iterations", 2)

# Mission Banner
status_badge_color = {
    "completed": "#10b981",
    "failed": "#f43f5e",
    "cancelled": "#f59e0b",
    "queued": "#94a3b8"
}.get(status, "#38bdf8")

st.markdown(
    f"""
    <div style="background: rgba(19, 23, 34, 0.8); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 10px; padding: 18px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.8rem; font-family: monospace; color: #a5b4fc;">JOB ID: {active_id}</span>
            <span style="background: rgba(255,255,255,0.06); color: {status_badge_color}; border: 1px solid {status_badge_color}; padding: 3px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">
                {status}
            </span>
        </div>
        <div style="font-size: 1.15rem; font-weight: 600; color: #f8fafc; margin-top: 8px;">
            {question}
        </div>
        <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 8px; display: flex; gap: 20px;">
            <span>⏱️ Iteration: <strong>{iteration}/{max_iter}</strong></span>
            <span>🌐 Sources: <strong>{len(sources)}</strong></span>
            <span>🛡️ Claims Audited: <strong>{len(claims)}</strong></span>
            <span>📋 Tasks Planned: <strong>{len(tasks)}</strong></span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Visual Pipeline Stage Indicator
pipeline_stages = [
    ("Supervisor", ["planning", "researching", "analyzing", "fact_checking", "reviewing", "generating_report", "completed"]),
    ("Researcher", ["researching", "analyzing", "fact_checking", "reviewing", "generating_report", "completed"]),
    ("Analyst", ["analyzing", "fact_checking", "reviewing", "generating_report", "completed"]),
    ("Fact Checker", ["fact_checking", "reviewing", "generating_report", "completed"]),
    ("Reviewer", ["reviewing", "generating_report", "completed"]),
    ("Report Generator", ["generating_report", "completed"])
]

# Map latest agent logs to agent cards
logs_by_agent = {}
for log in logs:
    agent_name = log.get("agent_name")
    logs_by_agent[agent_name] = log

def get_agent_display_state(agent_name: str, active_status: str):
    # Determine pending / running / completed / failed for this agent
    log = logs_by_agent.get(agent_name)
    if active_status == "failed" and log and log.get("status") == "failed":
        return "failed", log.get("input_summary"), log.get("error_message"), log.get("execution_time")
    if log and log.get("status") == "completed":
        return "completed", log.get("input_summary"), log.get("output_summary"), log.get("execution_time")

    # Current running node mapping
    agent_status_map = {
        "Supervisor": "planning",
        "Researcher": "researching",
        "Analyst": "analyzing",
        "Fact Checker": "fact_checking",
        "Reviewer": "reviewing",
        "Report Generator": "generating_report"
    }

    if active_status == agent_status_map.get(agent_name):
        return "running", "Currently executing assigned workflow node...", "Processing evidence in LangGraph state...", None

    return "pending", None, None, None

st.markdown("### 🤖 Autonomous Agent Squad")

col_a, col_b = st.columns(2)

agents_list = ["Supervisor", "Researcher", "Analyst", "Fact Checker", "Reviewer", "Report Generator"]

for idx, agent_name in enumerate(agents_list):
    st_status, task_desc, summary_text, dur = get_agent_display_state(agent_name, status)
    target_col = col_a if idx % 2 == 0 else col_b
    with target_col:
        render_agent_card(
            agent_name=agent_name,
            status=st_status,
            current_task=task_desc,
            summary=summary_text,
            duration=dur
        )

# Completed Callout and Quick Navigation
if status == "completed":
    st.balloons()
    st.success("🎉 Research mission completed! A structured, citation-backed intelligence report is ready.")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.info("👉 Switch to **3_📄_Research_Report** in the sidebar to read and export the full report.")
    with c2:
        st.info("👉 Switch to **4_🌐_Source_Explorer** to inspect deduplicated evidence and citations.")
elif status in ("queued", "planning", "researching", "analyzing", "fact_checking", "reviewing", "generating_report"):
    st.info("Agents are actively collaborating in the background. Click **'🔄 Refresh State'** above to monitor real-time updates.")
