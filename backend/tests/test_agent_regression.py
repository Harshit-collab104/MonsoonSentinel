import pytest
from fastapi.testclient import TestClient
import tempfile
import os

from app.api.main import app
from app.db.sqlite_repository import SqliteIncidentRepository
import app.db.sqlite_repository as db_module

@pytest.fixture
def test_client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    test_repo = SqliteIncidentRepository(path)
    db_module._default_repo = test_repo

    with TestClient(app) as client:
        yield client

    try:
        os.remove(path)
    except Exception:
        pass

def test_summary_question_returns_summary(test_client):
    # 1. Create incident
    rep = test_client.post("/api/v1/incidents", json={
        "reporter_name": "Test User",
        "reporter_phone": "9999999999",
        "ward_id": "WARD-TEST-01",
        "ward_name": "Test Ward",
        "latitude": 12.9,
        "longitude": 77.6,
        "drain_blockage_level": "COMPLETE",
        "water_depth_cm": 45.0,
        "description": "Culvert submerged",
        "landmark": "Test Landmark"
    }).json()
    inc_id = rep["id"]

    # 2. Ask summary question
    resp = test_client.post("/api/v1/agent/chat", json={
        "message": f"Can you give me an executive debrief and summary for {inc_id}?",
        "incident_id": inc_id
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "Executive Incident Debrief" in data["response"]
    assert inc_id in data["response"]
    assert "Test Ward" in data["response"]

def test_risk_question_invokes_risk_engine(test_client):
    rep = test_client.post("/api/v1/incidents", json={
        "reporter_name": "Test User",
        "reporter_phone": "9999999999",
        "ward_id": "WARD-TEST-02",
        "ward_name": "Risk Ward",
        "latitude": 12.9,
        "longitude": 77.6,
        "drain_blockage_level": "COMPLETE",
        "water_depth_cm": 50.0,
        "description": "Inundated storm culvert",
        "landmark": "Near Gate"
    }).json()
    inc_id = rep["id"]

    # Ask risk question
    resp = test_client.post("/api/v1/agent/chat", json={
        "message": f"What is the calculated risk score for {inc_id}?",
        "incident_id": inc_id
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "Risk" in data["response"] or "score" in data["response"].lower()
    # Risk engine was executed
    assert any("risk" in a.lower() for a in data.get("actions_taken", []))

def test_prioritization_question_compares_multiple_incidents(test_client):
    # Create two incidents
    i1 = test_client.post("/api/v1/incidents", json={
        "reporter_name": "User 1",
        "reporter_phone": "9999999991",
        "ward_id": "WARD-P1",
        "ward_name": "Ward High Risk",
        "latitude": 12.9,
        "longitude": 77.6,
        "drain_blockage_level": "COMPLETE",
        "water_depth_cm": 60.0,
        "description": "Deep flood",
        "landmark": "L1"
    }).json()["id"]

    i2 = test_client.post("/api/v1/incidents", json={
        "reporter_name": "User 2",
        "reporter_phone": "9999999992",
        "ward_id": "WARD-P2",
        "ward_name": "Ward Moderate Risk",
        "latitude": 13.0,
        "longitude": 77.7,
        "drain_blockage_level": "PARTIAL",
        "water_depth_cm": 15.0,
        "description": "Minor water",
        "landmark": "L2"
    }).json()["id"]

    # Calculate risk on both
    test_client.post(f"/api/v1/incidents/{i1}/analyze")
    test_client.post(f"/api/v1/incidents/{i2}/analyze")

    # Ask comparison question
    resp = test_client.post("/api/v1/agent/chat", json={
        "message": "Which incident has the highest risk? Compare all active incidents and rankings."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "Multi-Sector Incident Prioritization" in data["response"]
    assert i1 in data["response"]

def test_audit_question_retrieves_audit_records(test_client):
    rep = test_client.post("/api/v1/incidents", json={
        "reporter_name": "Audit Tester",
        "reporter_phone": "9999999999",
        "ward_id": "WARD-AUDIT",
        "ward_name": "Audit Ward",
        "latitude": 12.9,
        "longitude": 77.6,
        "drain_blockage_level": "SEVERE",
        "water_depth_cm": 30.0,
        "description": "Drain plugged",
        "landmark": "Audit Point"
    }).json()
    inc_id = rep["id"]

    # Advance state to generate audit trail
    test_client.post(f"/api/v1/incidents/{inc_id}/analyze")

    resp = test_client.post("/api/v1/agent/chat", json={
        "message": f"Show me the complete audit trail and history for {inc_id}",
        "incident_id": inc_id
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "Audit" in data["response"]
    assert any("audit" in a.lower() for a in data.get("actions_taken", []))

def test_flow_rate_question_returns_direct_concise_telemetry(test_client):
    rep = test_client.post("/api/v1/incidents", json={
        "reporter_name": "Flow Tester",
        "reporter_phone": "9999999999",
        "ward_id": "WARD-FLOW",
        "ward_name": "Flow Ward",
        "latitude": 12.9,
        "longitude": 77.6,
        "drain_blockage_level": "COMPLETE",
        "water_depth_cm": 35.0,
        "description": "Blockage",
        "landmark": "Culvert"
    }).json()
    inc_id = rep["id"]

    # Walk to VERIFIED state
    test_client.post(f"/api/v1/incidents/{inc_id}/analyze")
    test_client.post(f"/api/v1/incidents/{inc_id}/prioritize")
    test_client.post(f"/api/v1/incidents/{inc_id}/recommend")
    test_client.post(f"/api/v1/incidents/{inc_id}/approval", json={
        "approved": True,
        "reviewer": "Supervisor",
        "rationale": "Approve"
    })
    test_client.post(f"/api/v1/incidents/{inc_id}/tasks")
    test_client.post(f"/api/v1/incidents/{inc_id}/resolve", json={
        "resolution_notes": "Cleaned",
        "evidence_url": "s3://test/clean.jpg"
    })
    test_client.post(f"/api/v1/incidents/{inc_id}/verify", json={
        "sensor_flow_rate_lps": 85.0,
        "post_clearance_depth_cm": 0.5,
        "simulate_failure": False
    })

    # Ask specific flow rate question
    resp = test_client.post("/api/v1/agent/chat", json={
        "message": f"What was the final culvert flow rate recorded for {inc_id}?",
        "incident_id": inc_id
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "85.0 L/s" in data["response"]
    assert "Verified" in data["response"]
    # Ensure it's not a generic summary
    assert "Executive Incident Debrief" not in data["response"]

def test_archive_incident_lifecycle(test_client):
    rep = test_client.post("/api/v1/incidents", json={
        "reporter_name": "Archive Tester",
        "reporter_phone": "9999999999",
        "ward_id": "WARD-ARCHIVE",
        "ward_name": "Archive Ward",
        "latitude": 12.9,
        "longitude": 77.6,
        "drain_blockage_level": "CLEAR",
        "water_depth_cm": 0.0,
        "description": "Routine verification",
        "landmark": "Bridge"
    }).json()
    inc_id = rep["id"]

    # Walk to VERIFIED
    test_client.post(f"/api/v1/incidents/{inc_id}/analyze")
    test_client.post(f"/api/v1/incidents/{inc_id}/prioritize")
    test_client.post(f"/api/v1/incidents/{inc_id}/recommend")
    test_client.post(f"/api/v1/incidents/{inc_id}/approval", json={
        "approved": True, "reviewer": "Supervisor", "rationale": "Ok"
    })
    test_client.post(f"/api/v1/incidents/{inc_id}/tasks")
    test_client.post(f"/api/v1/incidents/{inc_id}/resolve", json={"resolution_notes": "Done"})
    test_client.post(f"/api/v1/incidents/{inc_id}/verify", json={
        "sensor_flow_rate_lps": 80.0, "post_clearance_depth_cm": 0.0, "simulate_failure": False
    })

    # Archive to S3
    archive_resp = test_client.post(f"/api/v1/incidents/{inc_id}/archive")
    assert archive_resp.status_code == 200
    arch_data = archive_resp.json()
    assert arch_data["archived"] is True
    assert arch_data["s3_archive_key"] == f"archives/{inc_id}.json"
    assert arch_data["purged_from_database"] is True

    # Confirm incident is purged from active database
    get_resp = test_client.get(f"/api/v1/incidents/{inc_id}")
    assert get_resp.status_code == 404
