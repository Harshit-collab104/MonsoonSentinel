import pytest
from fastapi.testclient import TestClient
import tempfile
import os

from app.api.main import app
from app.db.sqlite_repository import SqliteIncidentRepository, get_repository
import app.db.sqlite_repository as db_module

@pytest.fixture(scope="module")
def client():
    # Use temporary test database
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    test_repo = SqliteIncidentRepository(path)
    db_module._default_repo = test_repo

    with TestClient(app) as test_client:
        yield test_client

    try:
        os.remove(path)
    except Exception:
        pass

def test_full_api_workflow_end_to_end(client):
    # Step 1 & 2: Citizen submits report
    payload = {
        "reporter_name": "Arjun Singhal",
        "reporter_phone": "+91-99887-76655",
        "ward_id": "WARD-12",
        "ward_name": "Central Metro & Commercial Hub",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "drain_blockage_level": "COMPLETE",
        "water_depth_cm": 40.0,
        "description": "Massive plastic clogging at main culvert intake under flyover.",
        "landmark": "Near Metro Pillar 200"
    }
    create_resp = client.post("/api/v1/incidents", json=payload)
    assert create_resp.status_code == 201
    incident = create_resp.json()
    inc_id = incident["id"]
    assert incident["status"] == "NEW"

    # Step 3 & 4: Risk Analysis
    analyze_resp = client.post(f"/api/v1/incidents/{inc_id}/analyze")
    assert analyze_resp.status_code == 200
    analyzed = analyze_resp.json()
    assert analyzed["risk_assessment"] is not None
    assert analyzed["risk_assessment"]["risk_score"] > 0
    assert analyzed["risk_assessment"]["is_synthetic_data"] is True

    # Step 5: Prioritization
    prio_resp = client.post(f"/api/v1/incidents/{inc_id}/prioritize")
    assert prio_resp.status_code == 200
    prioritized = prio_resp.json()
    assert prioritized["priority"] is not None
    assert prioritized["priority"]["priority_rank"] >= 1

    # Step 6: Recommend response
    rec_resp = client.post(f"/api/v1/incidents/{inc_id}/recommend")
    assert rec_resp.status_code == 200
    recommended = rec_resp.json()
    assert recommended["status"] == "AWAITING_APPROVAL"
    assert recommended["recommended_action"] is not None

    # Step 7: Human supervisor review & approval
    appr_payload = {
        "approved": True,
        "reviewer": "Chief_Superintendent_Sharma",
        "rationale": "High flood danger to subway corridor; authorize Super-Sucker rig dispatch."
    }
    appr_resp = client.post(f"/api/v1/incidents/{inc_id}/approval", json=appr_payload)
    assert appr_resp.status_code == 200
    approved = appr_resp.json()
    assert approved["status"] == "IN_PROGRESS"
    assert approved["response_task"] is not None
    assert "NOT occurred yet" in approved["response_task"]["disclaimer"]

    # Step 8: Idempotent task creation test
    task_dup_resp = client.post(f"/api/v1/incidents/{inc_id}/tasks")
    assert task_dup_resp.status_code == 200
    assert task_dup_resp.json()["response_task"]["task_id"] == approved["response_task"]["task_id"]

    # Step 9: Field crew records resolution
    res_payload = {
        "resolution_notes": "Super-sucker extracted 3.5 cubic meters of silt. Flow normalized.",
        "evidence_url": "https://images.unsplash.com/clear_drain.jpg"
    }
    res_resp = client.post(f"/api/v1/incidents/{inc_id}/resolve", json=res_payload)
    assert res_resp.status_code == 200
    resolved = res_resp.json()
    assert resolved["status"] == "RESOLVED"

    # Step 10: Verification telemetry
    ver_payload = {
        "sensor_flow_rate_lps": 85.0,
        "post_clearance_depth_cm": 0.0,
        "simulate_failure": False
    }
    ver_resp = client.post(f"/api/v1/incidents/{inc_id}/verify", json=ver_payload)
    assert ver_resp.status_code == 200
    verified = ver_resp.json()
    assert verified["status"] == "VERIFIED"
    assert verified["verification"]["verified"] is True

    # Audit history inspection
    audit_resp = client.get(f"/api/v1/incidents/{inc_id}/audit")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert len(audit_data["audit_history"]) >= 6

    # Dynamic Stats inspection (derived dynamically)
    stats_resp = client.get("/api/v1/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_incidents"] >= 1
    assert stats["verified"] >= 1
