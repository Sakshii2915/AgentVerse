"""AgentVerse - Multi-Agent Research & Intelligence System Streamlit Landing Application."""

import streamlit as st
import os
import sys

# Add frontend directory to path
frontend_dir = os.path.dirname(os.path.abspath(__file__))
if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

from api_client import api_client
from components.header import render_header
from components.metrics import render_metric_card

# Configure Streamlit page
st.set_page_config(
    page_title="AgentVerse — Multi-Agent Research System",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom theme CSS
css_path = os.path.join(frontend_dir, "styles", "theme.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state keys
if "active_research_id" not in st.session_state:
    st.session_state.active_research_id = None
if "research_question" not in st.session_state:
    st.session_state.research_question = ""

render_header("Autonomous Multi-Agent Investigation & Synthesis Platform")

# Top telemetry overview
health = api_client.check_health()
history = api_client.get_history(limit=50)

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_metric_card("Total Investigations", str(len(history)), "Stored in Database")
with col2:
    completed = sum(1 for h in history if h.get("status") == "completed")
    render_metric_card("Completed Reports", str(completed), f"{int((completed/max(1, len(history)))*100)}% Success")
with col3:
    total_sources = sum(h.get("source_count", 0) for h in history)
    render_metric_card("Evidence Sources", str(total_sources), "Canonical Deduplicated")
with col4:
    provider_name = health.get("search_provider", "auto").upper()
    render_metric_card("Search Provider", provider_name, "Active Provider")

st.markdown("<br>", unsafe_allow_html=True)

# Quick Start Action / Mission Launcher
col_main, col_side = st.columns([2, 1])

with col_main:
    st.markdown("### 🚀 Initiate Autonomous Research")
    st.markdown(
        "Enter a complex topic, technology trend, or industry hypothesis. "
        "A team of six specialized LangGraph agents will independently plan, retrieve evidence, "
        "analyze trends, fact-check claims, peer-review findings, and publish an evidence-backed report."
    )

    sample_questions = [
        "Analyse the impact of generative AI on software engineering jobs over the next five years.",
        "Evaluate the commercial viability and timeline of solid-state lithium-metal batteries for electric aviation.",
        "Assess the post-quantum cryptography migration challenges for enterprise financial institutions by 2030.",
        "Compare small modular nuclear reactors (SMRs) against grid-scale battery storage for datacenter power."
    ]

    selected_sample = st.selectbox("Or choose an example research prompt:", ["Select an example..."] + sample_questions)
    default_text = selected_sample if selected_sample != "Select an example..." else ""

    user_query = st.text_area(
        "Research Objective or Prompt:",
        value=default_text,
        height=110,
        placeholder="e.g. Analyse the impact of generative AI on software engineering jobs over the next five years..."
    )

    depth_col, source_col = st.columns(2)
    with depth_col:
        depth = st.select_slider(
            "Investigation Depth:",
            options=["quick", "standard", "deep"],
            value="standard",
            help="Quick: 3 sources/subtopic. Standard: 5 sources. Deep: 8 sources with deep extraction."
        )
    with source_col:
        max_sources = st.slider("Target Canonical Sources:", min_value=6, max_value=25, value=12)

    if st.button("✨ Launch Research Mission", type="primary", use_container_width=True):
        if not user_query or len(user_query.strip()) < 5:
            st.error("Please enter a research prompt of at least 5 characters.")
        else:
            with st.spinner("Submitting mission to multi-agent orchestrator..."):
                try:
                    res = api_client.create_research(
                        research_question=user_query.strip(),
                        depth=depth,
                        max_sources=max_sources,
                        max_iterations=2
                    )
                    st.session_state.active_research_id = res["id"]
                    st.session_state.research_question = user_query.strip()
                    st.success(f"Mission initiated! Job ID: {res['id']}")
                    st.info("👉 Switch to the **'Live Agent Workspace'** page in the left sidebar to observe live agent collaboration!")
                except Exception as exc:
                    st.error(f"Failed to submit research mission: {exc}")

with col_side:
    st.markdown("### 🏛️ Agent Architecture")
    st.markdown(
        """
        AgentVerse coordinates a stateful LangGraph team:
        - 🧠 **Supervisor**: Strategic task decomposition
        - 🌐 **Researcher**: Web retrieval & canonical deduplication
        - 📊 **Analyst**: Empirical synthesis & gap identification
        - 🛡️ **Fact-Checker**: Claim auditing & contradiction detection
        - ⚖️ **Reviewer**: Quality control & dynamic loop routing
        - 📄 **Report Generator**: Publication with numbered citations
        """
    )
    st.markdown("---")
    st.markdown("### 🧭 Workspace Navigation")
    st.markdown(
        """
        - **1. Research Studio**: Configure & submit prompts
        - **2. Live Workspace**: Watch agents execute live
        - **3. Research Report**: View & download synthesis
        - **4. Source Explorer**: Inspect deduplicated sources
        - **5. Research History**: Reopen past investigations
        - **6. Agent Insights**: Analytics & telemetry charts
        """
    )

# Footer
st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("AgentVerse Multi-Agent Research System | Powered by LangGraph, FastAPI, and Streamlit")
