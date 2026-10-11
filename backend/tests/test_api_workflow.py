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

def test_api_gateway_stage_docs_and_root_routing(client):
    # Test root endpoint returns operational info and docs links
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    root_data = root_resp.json()
    assert root_data["system"] == "Monsoon Sentinel"
    assert "docs_url" in root_data
    assert "openapi_url" in root_data

    # Test OpenAPI schema endpoint returns HTTP 200 and includes incident routes
    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    openapi_spec = openapi_resp.json()
    assert "paths" in openapi_spec
    assert "/api/v1/incidents" in openapi_spec["paths"]

    # Test Swagger UI docs endpoint returns HTTP 200
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

def test_agent_structured_response_and_authoritative_state(client):
    # Create incident
    payload = {
        "reporter_name": "Kavita Rao",
        "reporter_phone": "+91-99000-11223",
        "ward_id": "WARD-07",
        "ward_name": "South Lakeside & Riverfront Drainage Basin",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "drain_blockage_level": "SEVERE",
        "water_depth_cm": 35.0,
        "description": "Lakeside culvert inlet heavily choked with tree limbs.",
        "landmark": "Near Lake Gate"
    }
    create_resp = client.post("/api/v1/incidents", json=payload)
    inc_id = create_resp.json()["id"]

    # 1. Test conversational chat endpoint returns structured fields
    chat_resp = client.post("/api/v1/agent/chat", json={
        "message": f"What is the status of {inc_id}?",
        "incident_id": inc_id
    })
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "response" in chat_data
    assert chat_data["incident_id"] == inc_id
    assert chat_data["incident_status"] == "NEW"
    assert "reasoning_summary" in chat_data
    assert "actions_taken" in chat_data
    assert "next_steps" in chat_data
    # Ensure no internal mock/SDK strings leaked into response text
    assert "running on local Strands Agents SDK" not in chat_data["response"]
    assert "thought_process" not in chat_data

    # 2. Test triage endpoint returns structured professional format
    triage_resp = client.post(f"/api/v1/incidents/{inc_id}/triage")
    assert triage_resp.status_code == 200
    triage_data = triage_resp.json()
    assert triage_data["incident_id"] == inc_id
    assert triage_data["incident_status"] == "AWAITING_APPROVAL"
    assert triage_data["risk_score"] > 0
    assert triage_data["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert len(triage_data["actions_taken"]) >= 4
    assert len(triage_data["next_steps"]) >= 1
    assert "debug" in triage_data

def test_human_review_supervisor_actions(client):
    # 1. Create and advance an incident to RESOLVED
    payload = {
        "reporter_name": "Rohan Deshmukh",
        "reporter_phone": "+91-98333-44556",
        "ward_id": "WARD-BOM-01",
        "ward_name": "Mumbai - Hindmata Cinema & Dadar TT Pumping Station",
        "latitude": 19.0178,
        "longitude": 72.8478,
        "drain_blockage_level": "COMPLETE",
        "water_depth_cm": 50.0,
        "description": "Hindmata flyover underpass flooding.",
        "landmark": "Dadar TT Circle"
    }
    create_resp = client.post("/api/v1/incidents", json=payload)
    inc_id = create_resp.json()["id"]

    client.post(f"/api/v1/incidents/{inc_id}/analyze")
    client.post(f"/api/v1/incidents/{inc_id}/prioritize")
    client.post(f"/api/v1/incidents/{inc_id}/recommend")
    client.post(f"/api/v1/incidents/{inc_id}/approval", json={
        "approved": True,
        "reviewer": "Chief_Dispatcher_Kapoor",
        "rationale": "Urgent dewatering needed."
    })
    client.post(f"/api/v1/incidents/{inc_id}/tasks")
    client.post(f"/api/v1/incidents/{inc_id}/resolve", json={
        "resolution_notes": "Silt cleared by suction truck.",
        "evidence_url": "s3://monsoon-sentinel-evidence/test.jpg"
    })

    # 2. Trigger failed verification -> transitions to NEEDS_HUMAN_REVIEW
    verify_resp = client.post(f"/api/v1/incidents/{inc_id}/verify", json={
        "sensor_flow_rate_lps": 12.0,
        "post_clearance_depth_cm": 15.0,
        "simulate_failure": True
    })
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "NEEDS_HUMAN_REVIEW"

    # 3. Test Redispatch endpoint -> moves back to IN_PROGRESS
    redispatch_resp = client.post(f"/api/v1/incidents/{inc_id}/redispatch", json={
        "reason": "Water depth still 15cm; desilt second culvert intake.",
        "reviewer": "Supervisor_Kapoor"
    })
    assert redispatch_resp.status_code == 200
    assert redispatch_resp.json()["status"] == "IN_PROGRESS"

    # Re-resolve and re-fail to test override verify
    client.post(f"/api/v1/incidents/{inc_id}/resolve", json={
        "resolution_notes": "Secondary desilting complete."
    })
    client.post(f"/api/v1/incidents/{inc_id}/verify", json={
        "sensor_flow_rate_lps": 12.0,
        "post_clearance_depth_cm": 6.0,
        "simulate_failure": True
    })

    # 4. Test Override Verify endpoint -> moves to VERIFIED
    override_resp = client.post(f"/api/v1/incidents/{inc_id}/override-verify", json={
        "reviewer": "Chief_Engineer_Rao",
        "rationale": "Manual visual inspection confirmed storm drain clear; sensor is calibrated."
    })
    assert override_resp.status_code == 200
    assert override_resp.json()["status"] == "VERIFIED"
    assert override_resp.json()["verification"]["verified"] is True

