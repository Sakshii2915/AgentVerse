"""Page 3: Research Report - Structured Synthesis & Executive Publication."""

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

st.set_page_config(page_title="Research Report — AgentVerse", page_icon="📄", layout="wide")

# Theme styling
css_path = os.path.join(parent_dir, "styles", "theme.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

render_header("Executive Intelligence Report")

active_id = st.session_state.get("active_research_id")

history = api_client.get_history(limit=25)
job_options = {h["id"]: f"{h['research_question'][:60]}... ({h['status'].upper()})" for h in history}

if not job_options and not active_id:
    st.info("No research sessions available. Please initiate research in **1_🔬_Research_Studio**.")
    st.stop()

# Context selector
c1, c2 = st.columns([3, 1])
with c1:
    selected_id = st.selectbox(
        "Select Research Mission to View:",
        options=list(job_options.keys()),
        index=list(job_options.keys()).index(active_id) if active_id in job_options else 0,
        format_func=lambda x: job_options.get(x, x)
    )
    if selected_id != active_id:
        st.session_state.active_research_id = selected_id
        active_id = selected_id

with c2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Report", use_container_width=True):
        st.rerun()

# Fetch report from backend
report_data = api_client.get_research_report(active_id)
job_data = api_client.get_history_detail(active_id)

if not report_data:
    st.warning("No completed report is currently available for this research mission. It may still be in progress or failed.")
    st.info("👉 Check current progress in **2_⚡_Live_Agent_Workspace**.")
    st.stop()

if report_data.get("status") == "in_progress":
    st.info("⏳ Agents are currently synthesizing this report. Please refresh in a few moments.")
    st.stop()

# Header metadata
report_content = report_data.get("report_content", "")
executive_summary = report_data.get("executive_summary", "")
methodology = report_data.get("methodology", "")
key_findings = report_data.get("key_findings", [])
risks_opps = report_data.get("risks_opportunities", {})
limitations = report_data.get("limitations", "")
citations_json = report_data.get("citations_json", [])
sources = job_data.get("sources", []) if job_data else []

# Action Buttons: Download Markdown, Download PDF, Copy Content
act_col1, act_col2, act_col3 = st.columns([1, 1, 1])

with act_col1:
    st.download_button(
        label="📥 Download Markdown",
        data=report_content,
        file_name=f"AgentVerse_Report_{active_id[:8]}.md",
        mime="text/markdown",
        use_container_width=True
    )

with act_col2:
    pdf_bytes = api_client.get_report_pdf_bytes(active_id)
    if pdf_bytes:
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"AgentVerse_Report_{active_id[:8]}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.button("📄 PDF Processing...", disabled=True, use_container_width=True)

with act_col3:
    if st.button("📋 Copy Report to Clipboard", use_container_width=True):
        st.toast("Report markdown ready to copy from the raw viewer below!")

# Executive Summary Callout
st.markdown("### 📌 Executive Summary")
st.markdown(
    f"""
    <div class="executive-summary-box">
        <div style="font-size: 1.05rem; color: #f1f5f9; line-height: 1.7;">
            {executive_summary}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Render Full Report Tabs
tab_report, tab_sources, tab_raw = st.tabs(["📖 Full Structured Report", "🔗 Verified References", "💻 Raw Markdown"])

with tab_report:
    st.markdown(report_content)

with tab_sources:
    st.markdown("### 📚 Verifiable Research Citations")
    st.markdown("Every factual claim in the report corresponds to one of the following canonical sources:")

    display_citations = citations_json if citations_json else sources
    if not display_citations:
        st.info("No external citations registered.")
    else:
        for idx, cit in enumerate(display_citations, 1):
            num = cit.get("number") or cit.get("citation_number", idx)
            title = cit.get("title", "Untitled Source")
            domain = cit.get("domain", "web")
            url = cit.get("url", "#")
            pub_date = cit.get("publication_date")
            date_str = f" • Published: {pub_date}" if pub_date else ""

            st.markdown(
                f"""
                <div class="source-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <span class="citation-tag">[{num}]</span>
                            <strong style="color: #f8fafc; font-size: 0.95rem; margin-left: 8px;">{title}</strong>
                        </div>
                        <span class="source-domain-pill">{domain}</span>
                    </div>
                    <div style="margin-top: 6px; font-size: 0.8rem; color: #94a3b8;">
                        <a href="{url}" target="_blank" style="color: #38bdf8; text-decoration: none;">🔗 {url}</a>
                        {date_str}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

with tab_raw:
    st.code(report_content, language="markdown")
