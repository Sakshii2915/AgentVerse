"""Brand header component with editorial research aesthetic."""

import streamlit as st
from api_client import api_client


def render_header(subtitle: str = "Multi-Agent Research & Intelligence System"):
    """Render top editorial brand bar."""
    health = api_client.check_health()
    is_online = health.get("status") == "healthy"
    provider = health.get("search_provider", "auto")

    status_color = "#34d399" if is_online else "#f87171"
    status_text = f"Connected ({provider.upper()})" if is_online else "Backend Offline"

    st.markdown(
        f"""
        <div class="brand-header-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="brand-badge">Autonomous Intelligence Platform</div>
                    <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #f8fafc;">
                        Agent<span style="color: #8b5cf6;">Verse</span>
                    </h1>
                    <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.95rem;">
                        {subtitle}
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(15, 23, 42, 0.6); padding: 6px 12px; border-radius: 9999px; border: 1px solid rgba(255, 255, 255, 0.1);">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background-color: {status_color}; display: inline-block;"></span>
                        <span style="font-size: 0.75rem; font-family: monospace; color: #cbd5e1;">{status_text}</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
