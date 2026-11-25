"""Metric and telemetry summary card components."""

import streamlit as st


def render_metric_card(label: str, value: str, subtext: str = ""):
    """Render a styled metric box."""
    st.markdown(
        f"""
        <div class="stat-box">
            <div class="stat-val">{value}</div>
            <div class="stat-lbl">{label}</div>
            {f'<div style="font-size: 0.72rem; color: #64748b; margin-top: 4px;">{subtext}</div>' if subtext else ''}
        </div>
        """,
        unsafe_allow_html=True
    )
