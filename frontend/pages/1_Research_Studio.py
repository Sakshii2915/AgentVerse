"""Page 1: Research Studio - Submission and Configuration Portal."""

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

st.set_page_config(page_title="Research Studio — AgentVerse", page_icon="🔬", layout="wide")

# Theme styling
css_path = os.path.join(parent_dir, "styles", "theme.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

render_header("Studio: Configure & Launch Multi-Agent Investigations")

st.markdown("## 🔬 New Research Mission")
st.markdown("Specify your target research domain, prompt, and investigation rigor.")

# Example Prompts
examples = {
    "Generative AI & Software Engineering": "Analyse the impact of generative AI on software engineering jobs over the next five years.",
    "Solid-State Batteries & Aviation": "Evaluate the commercial viability and timeline of solid-state lithium-metal batteries for electric aviation.",
    "Post-Quantum Cryptography": "Assess the post-quantum cryptography migration challenges for enterprise financial institutions by 2030.",
    "Nuclear SMRs vs Battery Storage": "Compare small modular nuclear reactors (SMRs) against grid-scale battery storage for datacenter power.",
    "Brain-Computer Interfaces": "Investigate the current clinical readiness and ethical dilemmas surrounding invasive brain-computer interfaces (BCIs)."
}

selected_example_label = st.selectbox(
    "💡 Quick-fill from curated research prompts:",
    ["Custom Prompt..."] + list(examples.keys())
)

default_text = ""
if selected_example_label != "Custom Prompt...":
    default_text = examples[selected_example_label]

research_prompt = st.text_area(
    "Detailed Research Objective:",
    value=default_text,
    height=130,
    placeholder="Enter an in-depth analytical question or technology investigation prompt..."
)

col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
with col_cfg1:
    depth = st.select_slider(
        "Investigation Depth",
        options=["quick", "standard", "deep"],
        value="standard",
        help="Controls number of queries per subtopic and web text extraction depth."
    )
with col_cfg2:
    max_sources = st.slider(
        "Maximum Total Sources",
        min_value=6,
        max_value=30,
        value=12,
        help="Global ceiling on unique canonical sources retrieved across all subtopics."
    )
with col_cfg3:
    max_iterations = st.number_input(
        "Maximum Revision Loops",
        min_value=1,
        max_value=4,
        value=2,
        help="Bound on Reviewer-triggered feedback loops to prevent runaway execution."
    )

if st.button("🚀 Start Autonomous Research", type="primary", use_container_width=True):
    if not research_prompt or len(research_prompt.strip()) < 5:
        st.warning("Please provide a meaningful research prompt (at least 5 characters).")
    else:
        with st.spinner("Initializing multi-agent team..."):
            try:
                res = api_client.create_research(
                    research_question=research_prompt.strip(),
                    depth=depth,
                    max_sources=max_sources,
                    max_iterations=max_iterations
                )
                st.session_state.active_research_id = res["id"]
                st.session_state.research_question = research_prompt.strip()
                st.success(f"Research job created successfully! ID: `{res['id']}`")
                st.info("👉 Navigating to Live Agent Workspace...")
                st.markdown(
                    f"""
                    <div style="background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.4); padding: 14px; border-radius: 8px; margin-top: 10px;">
                        <strong>Job ID:</strong> <code>{res['id']}</code><br>
                        <strong>Prompt:</strong> {research_prompt[:120]}...<br>
                        <em>Click on <strong>'2_⚡_Live_Agent_Workspace'</strong> in the left sidebar to watch agents execute.</em>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            except Exception as exc:
                st.error(f"Error submitting research: {exc}")

st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📚 Recent Research Sessions")

history = api_client.get_history(limit=6)
if not history:
    st.info("No prior research sessions recorded yet. Launch your first mission above!")
else:
    cols = st.columns(3)
    for idx, item in enumerate(history):
        col = cols[idx % 3]
        with col:
            status_color = "#34d399" if item.get("status") == "completed" else "#38bdf8"
            st.markdown(
                f"""
                <div class="source-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 0.75rem; color: #64748b; font-family: monospace;">{item['created_at'][:10]}</span>
                        <span style="font-size: 0.72rem; padding: 2px 8px; border-radius: 9999px; background: rgba(56, 189, 248, 0.1); color: {status_color}; font-weight: 600;">{item['status'].upper()}</span>
                    </div>
                    <div style="font-weight: 600; font-size: 0.92rem; color: #f8fafc; height: 50px; overflow: hidden; text-overflow: ellipsis;">
                        {item['research_question'][:80]}...
                    </div>
                    <div style="margin-top: 10px; font-size: 0.78rem; color: #94a3b8; display: flex; gap: 12px;">
                        <span>📚 {item.get('source_count', 0)} sources</span>
                        <span>🛡️ {item.get('claim_count', 0)} claims</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Open Session", key=f"open_btn_{item['id']}"):
                st.session_state.active_research_id = item["id"]
                st.session_state.research_question = item["research_question"]
                st.info(f"Loaded session `{item['id']}` into active context. Switch to pages 2, 3, or 4!")
