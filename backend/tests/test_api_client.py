"""Test Streamlit API client methods."""

import sys
import os
import pytest

# Ensure frontend path is accessible
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if frontend_path not in sys.path:
    sys.path.insert(0, frontend_path)

from api_client import AgentVerseAPIClient


def test_api_client_instantiation():
    client = AgentVerseAPIClient(base_url="http://localhost:8000")
    assert client.base_url == "http://localhost:8000"


def test_api_client_offline_handling():
    # Connecting to an unrouted port should return offline status gracefully without crashing
    client = AgentVerseAPIClient(base_url="http://localhost:59999")
    res = client.check_health()
    assert res.get("status") == "offline"
