import pytest
import tempfile
import os
from app.db.sqlite_repository import SqliteIncidentRepository
from app.services.incident_service import IncidentService
from app.models.incident import CitizenReportCreate
from app.core.enums import IncidentStatus, BlockageSeverity

@pytest.fixture
def service():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    repo = SqliteIncidentRepository(path)
    svc = IncidentService(repo)
    yield svc
    try:
        os.remove(path)
    except Exception:
        pass

def _setup_resolved_incident(service):
    report = CitizenReportCreate(
        reporter_name="Citizen",
        ward_id="WARD-12",
        ward_name="Central Metro",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.SEVERE,
        description="Drain blockage test"
    )
    inc = service.create_incident(report)
    service.analyze_risk(inc.id)
    service.prioritize_incident(inc.id)
    service.generate_recommendation(inc.id)
    service.submit_for_human_approval(inc.id)
    service.review_human_approval(inc.id, approved=True, reviewer="Officer", rationale="Approved")
    service.record_resolution(inc.id, resolution_notes="Completed drain clearance.")
    return inc

def test_successful_verification(service):
    inc = _setup_resolved_incident(service)
    verified_inc = service.verify_resolution(
        inc.id,
        sensor_flow_rate_lps=80.0,
        post_clearance_depth_cm=0.5
    )
    assert verified_inc.status == IncidentStatus.VERIFIED
    assert verified_inc.verification.verified is True
    assert verified_inc.verification.simulated is True

def test_failed_verification_transitions_to_needs_human_review(service):
    inc = _setup_resolved_incident(service)
    # Post-clearance depth of 15cm indicates water did not recede
    failed_inc = service.verify_resolution(
        inc.id,
        sensor_flow_rate_lps=5.0,
        post_clearance_depth_cm=15.0
    )
    assert failed_inc.status == IncidentStatus.NEEDS_HUMAN_REVIEW
    assert failed_inc.verification.verified is False
    assert "Verification failed" in failed_inc.audit_history[-1].reason
