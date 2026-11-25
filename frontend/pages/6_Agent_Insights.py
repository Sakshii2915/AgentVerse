"""Page 6: Agent Insights - System Telemetry, Verification Analytics & Charts."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Ensure frontend root is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from api_client import api_client
from components.header import render_header
from components.metrics import render_metric_card

st.set_page_config(page_title="Agent Insights — AgentVerse", page_icon="📊", layout="wide")

# Theme styling
css_path = os.path.join(parent_dir, "styles", "theme.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

render_header("Agent Insights: System Telemetry & Analytical Performance")

history = api_client.get_history(limit=100)

if not history:
    st.info("No research telemetry accumulated yet. Run a research mission to generate analytical insights!")
    st.stop()

# Aggregate stats
total_runs = len(history)
completed_runs = sum(1 for h in history if h.get("status") == "completed")
failed_runs = sum(1 for h in history if h.get("status") == "failed")
running_runs = total_runs - completed_runs - failed_runs
total_sources = sum(h.get("source_count", 0) for h in history)
total_claims = sum(h.get("claim_count", 0) for h in history)

# Metric row
m1, m2, m3, m4 = st.columns(4)
with m1:
    render_metric_card("Total Missions", str(total_runs), "All Time Executions")
with m2:
    success_rate = int((completed_runs / max(1, total_runs)) * 100)
    render_metric_card("Mission Success Rate", f"{success_rate}%", f"{completed_runs} Completed / {failed_runs} Failed")
with m3:
    render_metric_card("Total Sources Indexed", str(total_sources), "Canonical Deduplicated")
with m4:
    render_metric_card("Claims Audited", str(total_claims), "Verified by Fact-Checker")

st.markdown("<br>", unsafe_allow_html=True)

# Visual Charts with Plotly
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("### 🎯 Mission Status Breakdown")
    status_df = pd.DataFrame([
        {"Status": "Completed", "Count": completed_runs, "Color": "#10b981"},
        {"Status": "Failed", "Count": failed_runs, "Color": "#f43f5e"},
        {"Status": "Active/Other", "Count": running_runs, "Color": "#38bdf8"}
    ])
    status_df = status_df[status_df["Count"] > 0]

    fig_pie = px.pie(
        status_df,
        names="Status",
        values="Count",
        color="Status",
        color_discrete_map={"Completed": "#10b981", "Failed": "#f43f5e", "Active/Other": "#38bdf8"},
        hole=0.45
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f1f5f9"),
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with chart_col2:
    st.markdown("### 🌐 Sources & Claims by Session")
    session_data = []
    for h in history[:10]:
        session_data.append({
            "Mission": h["research_question"][:25] + "...",
            "Sources": h.get("source_count", 0),
            "Claims": h.get("claim_count", 0)
        })
    sess_df = pd.DataFrame(session_data)
    if not sess_df.empty:
        fig_bar = px.bar(
            sess_df,
            x="Mission",
            y=["Sources", "Claims"],
            barmode="group",
            color_discrete_map={"Sources": "#8b5cf6", "Claims": "#38bdf8"}
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f1f5f9"),
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#1e293b")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# Agent Execution Duration Analytics
st.markdown("### ⚡ Agent Execution Telemetry")
active_id = st.session_state.get("active_research_id") or (history[0]["id"] if history else None)

if active_id:
    logs = api_client.get_agent_logs(active_id)
    if logs:
        log_df = pd.DataFrame([
            {
                "Agent": l["agent_name"],
                "Duration (s)": l["execution_time"],
                "Status": l["status"].upper()
            }
            for l in logs
        ])
        fig_dur = px.bar(
            log_df,
            x="Agent",
            y="Duration (s)",
            color="Agent",
            text="Duration (s)",
            color_discrete_sequence=["#8b5cf6", "#6366f1", "#38bdf8", "#06b6d4", "#10b981", "#f59e0b"]
        )
        fig_dur.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f1f5f9"),
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#1e293b")
        )
        st.plotly_chart(fig_dur, use_container_width=True)
    else:
        st.info("No granular execution duration logs for current selected session.")
