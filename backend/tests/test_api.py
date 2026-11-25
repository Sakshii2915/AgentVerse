"""Test FastAPI Endpoints and Background Research Execution."""

import pytest
from app.models.models import ResearchJob, ResearchReport, ResearchSource, AgentExecutionLog


def test_health_endpoint(client):
    """Verify system health endpoint returns operational metadata."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "version" in data
    assert "search_provider" in data
    assert "database_connected" in data
    assert data["database_connected"] is True


def test_create_research_job_endpoint(client, db_session):
    """Test job submission endpoint."""
    payload = {
        "research_question": "Evaluate the commercial viability of solid-state lithium-metal batteries for electric aviation.",
        "depth": "quick",
        "max_sources": 8,
        "max_iterations": 2
    }
    resp = client.post("/api/research", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["research_question"] == payload["research_question"]
    assert data["status"] in ("queued", "planning")


def test_get_research_status_and_not_found(client, db_session):
    """Test status query and 404 on nonexistent ID."""
    # 404 test
    resp = client.get("/api/research/nonexistent-uuid-999")
    assert resp.status_code == 404

    # Existing job
    job = ResearchJob(
        research_question="Quantum computing timeline",
        status="planning"
    )
    db_session.add(job)
    db_session.commit()

    resp = client.get(f"/api/research/{job.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job.id
    assert data["status"] == "planning"


def test_research_history_and_deletion(client, db_session):
    """Test research history listing and deletion."""
    job1 = ResearchJob(research_question="Topic 1", status="completed")
    job2 = ResearchJob(research_question="Topic 2", status="failed")
    db_session.add_all([job1, job2])
    db_session.commit()

    # List history
    resp = client.get("/api/research/history")
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) >= 2

    # Delete job1
    del_resp = client.delete(f"/api/research/history/{job1.id}")
    assert del_resp.status_code == 200

    # Verify job1 deleted
    get_resp = client.get(f"/api/research/{job1.id}")
    assert get_resp.status_code == 404


def test_cancel_research_endpoint(client, db_session):
    """Test cancel research job endpoint."""
    job = ResearchJob(research_question="Long running topic", status="researching")
    db_session.add(job)
    db_session.commit()

    resp = client.post(f"/api/research/{job.id}/cancel")
    assert resp.status_code == 200

    db_session.refresh(job)
    assert job.status == "cancelled"


def test_get_report_and_sources_endpoints(client, db_session):
    """Test report retrieval and sources listing."""
    job = ResearchJob(research_question="Completed Mission", status="completed")
    db_session.add(job)
    db_session.commit()

    # Add source
    source = ResearchSource(
        research_id=job.id,
        title="Source Alpha",
        url="https://alpha.example.org",
        canonical_url="https://alpha.example.org",
        domain="alpha.example.org",
        extracted_content="Alpha evidence",
        relevance_score=0.9,
        citation_number=1
    )
    report = ResearchReport(
        research_id=job.id,
        report_content="# Final Report Content",
        executive_summary="Summary of findings."
    )
    db_session.add_all([source, report])
    db_session.commit()

    # Get sources
    src_resp = client.get(f"/api/research/{job.id}/sources")
    assert src_resp.status_code == 200
    src_data = src_resp.json()
    assert len(src_data) == 1
    assert src_data[0]["title"] == "Source Alpha"

    # Get report
    rep_resp = client.get(f"/api/research/{job.id}/report")
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert rep_data["executive_summary"] == "Summary of findings."
