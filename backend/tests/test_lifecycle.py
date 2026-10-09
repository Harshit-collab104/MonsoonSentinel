import pytest
import tempfile
import os
from app.db.sqlite_repository import SqliteIncidentRepository
from app.services.incident_service import IncidentService
from app.models.incident import CitizenReportCreate
from app.core.enums import IncidentStatus, BlockageSeverity
from app.core.exceptions import InvalidStateTransitionError

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

def test_full_lifecycle_progression(service):
    report = CitizenReportCreate(
        reporter_name="Civic Reporter",
        ward_id="WARD-12",
        ward_name="Central Metro",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.SEVERE,
        water_depth_cm=35.0,
        description="Drain blocked near underpass"
    )

    # 1. NEW
    inc = service.create_incident(report)
    assert inc.status == IncidentStatus.NEW
    assert len(inc.audit_history) == 1

    # 2. ANALYZING
    inc = service.analyze_risk(inc.id)
    assert inc.status == IncidentStatus.ANALYZING
    assert inc.risk_assessment is not None

    # 3. PRIORITIZED
    inc = service.prioritize_incident(inc.id)
    assert inc.status == IncidentStatus.PRIORITIZED
    assert inc.priority is not None

    # 4. RECOMMENDED
    inc = service.generate_recommendation(inc.id)
    assert inc.status == IncidentStatus.RECOMMENDED
    assert inc.recommended_action is not None

    # 5. AWAITING_APPROVAL
    inc = service.submit_for_human_approval(inc.id)
    assert inc.status == IncidentStatus.AWAITING_APPROVAL

    # 6. APPROVED -> IN_PROGRESS (automatically dispatches task)
    inc = service.review_human_approval(
        inc.id, approved=True, reviewer="Officer_Rao", rationale="Approved for emergency dewatering"
    )
    assert inc.status == IncidentStatus.IN_PROGRESS
    assert inc.response_task is not None
    assert inc.response_task.status == "DISPATCHED"

    # 7. RESOLVED
    inc = service.record_resolution(inc.id, resolution_notes="Debris extracted, suction pump cleared pipe.")
    assert inc.status == IncidentStatus.RESOLVED

    # 8. VERIFIED
    inc = service.verify_resolution(inc.id, sensor_flow_rate_lps=60.0, post_clearance_depth_cm=1.0)
    assert inc.status == IncidentStatus.VERIFIED
    assert inc.verification.verified is True

def test_rejection_branch(service):
    report = CitizenReportCreate(
        reporter_name="Reporter",
        ward_id="WARD-19",
        ward_name="Eastern Hills",
        latitude=12.9850,
        longitude=77.6680,
        drain_blockage_level=BlockageSeverity.CLEAR,
        description="Puddle after rain"
    )
    inc = service.create_incident(report)
    service.analyze_risk(inc.id)
    service.prioritize_incident(inc.id)
    service.generate_recommendation(inc.id)
    service.submit_for_human_approval(inc.id)

    # Rejection
    inc = service.review_human_approval(
        inc.id, approved=False, reviewer="Supervisor_Mehta", rationale="Drain is already clear; natural runoff."
    )
    assert inc.status == IncidentStatus.REJECTED

def test_invalid_transition_rejected(service):
    report = CitizenReportCreate(
        reporter_name="Reporter",
        ward_id="WARD-12",
        ward_name="Central Metro",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.PARTIAL,
        description="Drain test"
    )
    inc = service.create_incident(report)
    # Directly attempting to resolve NEW incident without approval must fail
    with pytest.raises(InvalidStateTransitionError):
        service.record_resolution(inc.id, resolution_notes="Trying to resolve unapproved incident")
