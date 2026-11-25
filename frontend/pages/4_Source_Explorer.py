"""Page 4: Source Explorer - Research Library & Evidence Attribution."""

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

st.set_page_config(page_title="Source Explorer — AgentVerse", page_icon="🌐", layout="wide")

# Theme styling
css_path = os.path.join(parent_dir, "styles", "theme.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

render_header("Source Explorer: Verifiable Evidence Library")

active_id = st.session_state.get("active_research_id")

history = api_client.get_history(limit=25)
job_options = {h["id"]: f"{h['research_question'][:60]}... ({h['status'].upper()})" for h in history}

if not job_options and not active_id:
    st.info("No research missions found. Please launch a mission in **1_🔬_Research_Studio**.")
    st.stop()

# Header selector
col_sel, col_stat = st.columns([3, 1])
with col_sel:
    selected_id = st.selectbox(
        "Select Investigation Session:",
        options=list(job_options.keys()),
        index=list(job_options.keys()).index(active_id) if active_id in job_options else 0,
        format_func=lambda x: job_options.get(x, x)
    )
    if selected_id != active_id:
        st.session_state.active_research_id = selected_id
        active_id = selected_id

job_data = api_client.get_history_detail(active_id)
if not job_data:
    st.warning("Could not fetch evidence records for this mission.")
    st.stop()

sources = job_data.get("sources", [])
claims = job_data.get("claims", [])

with col_stat:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    st.markdown(f"**Total Sources:** `{len(sources)}` | **Claims:** `{len(claims)}`")

# Search and filter bar
f_col1, f_col2, f_col3 = st.columns([2, 1, 1])

with f_col1:
    search_keyword = st.text_input("🔍 Search within source titles or extracted text:", placeholder="e.g. productivity, benchmark...")

with f_col2:
    all_domains = sorted(list({s.get("domain", "web") for s in sources}))
    domain_filter = st.selectbox("Filter by Domain:", ["All Domains"] + all_domains)

with f_col3:
    min_score = st.slider("Min Relevance Score:", min_value=0.0, max_value=1.0, value=0.0, step=0.05)

# Filter sources
filtered = []
for s in sources:
    if domain_filter != "All Domains" and s.get("domain") != domain_filter:
        continue
    if s.get("relevance_score", 0.0) < min_score:
        continue
    if search_keyword:
        kw = search_keyword.lower()
        title_match = kw in s.get("title", "").lower()
        content_match = kw in s.get("extracted_content", "").lower()
        if not (title_match or content_match):
            continue
    filtered.append(s)

st.markdown(f"Displaying **{len(filtered)}** of **{len(sources)}** deduplicated sources:")

if not filtered:
    st.info("No sources match the selected filter criteria.")
else:
    for s in filtered:
        cit_num = s.get("citation_number", "—")
        title = s.get("title", "Untitled Source")
        url = s.get("url", "#")
        domain = s.get("domain", "unknown")
        rel = s.get("relevance_score", 0.5)
        content = s.get("extracted_content", "")
        pub_date = s.get("publication_date")
        date_str = f" • Published: {pub_date}" if pub_date else ""

        # Find associated claims that cite this source
        associated_claims = []
        for c in claims:
            # Check citation number in supporting_source_ids
            supporting = c.get("supporting_source_ids", [])
            if cit_num in supporting or str(cit_num) in [str(x) for x in supporting]:
                associated_claims.append(c)

        st.markdown(
            f"""
            <div class="source-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span class="citation-tag">[{cit_num}]</span>
                        <strong style="color: #f8fafc; font-size: 1.05rem; margin-left: 6px;">{title}</strong>
                    </div>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <span style="font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; background: rgba(56, 189, 248, 0.1); color: #38bdf8;">
                            Relevance: {int(rel * 100)}%
                        </span>
                        <span class="source-domain-pill">{domain}</span>
                    </div>
                </div>
                <div style="margin: 6px 0 10px 0; font-size: 0.82rem; color: #94a3b8;">
                    <a href="{url}" target="_blank" style="color: #6366f1; text-decoration: none;">🔗 {url}</a>
                    {date_str}
                </div>
                <div style="background: rgba(0, 0, 0, 0.25); border-radius: 6px; padding: 10px; font-size: 0.85rem; color: #cbd5e1; line-height: 1.5;">
                    <strong style="color: #a5b4fc;">Evidence Snippet:</strong> {content[:350]}...
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if associated_claims:
            with st.expander(f"🛡️ Verified Claims Associated with [{cit_num}] ({len(associated_claims)})"):
                for ac in associated_claims:
                    st_color = "#34d399" if ac.get("verification_status") == "supported" else "#fb7185"
                    st.markdown(
                        f"- <span style='color: {st_color}; font-weight: 600;'>[{ac.get('verification_status').upper()}]</span> {ac.get('claim_text')}",
                        unsafe_allow_html=True
                    )
