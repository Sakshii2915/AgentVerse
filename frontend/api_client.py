"""AgentVerse HTTP API Client for Streamlit Frontend with graceful offline resilience."""

import os
import requests
from typing import Dict, Any, Optional, List

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class AgentVerseAPIClient:
    """Client for interacting with the AgentVerse FastAPI backend."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> Dict[str, Any]:
        """Check backend status and configuration."""
        try:
            resp = requests.get(f"{self.base_url}/api/health", timeout=3)
            if resp.status_code == 200:
                return resp.json()
            return {"status": "error", "message": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}

    def create_research(
        self,
        research_question: str,
        depth: str = "standard",
        max_sources: int = 12,
        max_iterations: int = 2
    ) -> Dict[str, Any]:
        """Submit a new research mission."""
        payload = {
            "research_question": research_question,
            "depth": depth,
            "max_sources": max_sources,
            "max_iterations": max_iterations
        }
        try:
            resp = requests.post(f"{self.base_url}/api/research", json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            raise RuntimeError(f"Could not connect to backend at {self.base_url}: {exc}")

    def get_research_status(self, research_id: str) -> Dict[str, Any]:
        """Get live status and progress of a research job."""
        try:
            resp = requests.get(f"{self.base_url}/api/research/{research_id}", timeout=6)
            if resp.status_code == 200:
                return resp.json()
            return {"id": research_id, "status": "unknown"}
        except Exception:
            return {"id": research_id, "status": "offline"}

    def get_research_report(self, research_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve completed research report."""
        try:
            resp = requests.get(f"{self.base_url}/api/research/{research_id}/report", timeout=10)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 202:
                return {"status": "in_progress"}
            return None
        except Exception:
            return None

    def get_report_pdf_bytes(self, research_id: str) -> Optional[bytes]:
        """Download generated PDF bytes."""
        try:
            resp = requests.get(f"{self.base_url}/api/research/{research_id}/report/pdf", timeout=15)
            if resp.status_code == 200:
                return resp.content
            return None
        except Exception:
            return None

    def get_sources(self, research_id: str) -> List[Dict[str, Any]]:
        """Retrieve collected evidence sources."""
        try:
            resp = requests.get(f"{self.base_url}/api/research/{research_id}/sources", timeout=8)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception:
            return []

    def get_agent_logs(self, research_id: str) -> List[Dict[str, Any]]:
        """Retrieve agent execution logs."""
        try:
            resp = requests.get(f"{self.base_url}/api/research/{research_id}/agents", timeout=8)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception:
            return []

    def get_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve past research missions."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/research/history",
                params={"limit": limit, "offset": offset},
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception:
            return []

    def get_history_detail(self, research_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve complete mission details with all associated relations."""
        try:
            resp = requests.get(f"{self.base_url}/api/research/history/{research_id}", timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    def delete_history_item(self, research_id: str) -> bool:
        """Delete a research session."""
        try:
            resp = requests.delete(f"{self.base_url}/api/research/history/{research_id}", timeout=6)
            return resp.status_code == 200
        except Exception:
            return False

    def cancel_research(self, research_id: str) -> bool:
        """Cancel a running research mission."""
        try:
            resp = requests.post(f"{self.base_url}/api/research/{research_id}/cancel", timeout=6)
            return resp.status_code == 200
        except Exception:
            return False


api_client = AgentVerseAPIClient()
