import pytest
import tempfile
import os
from app.db.sqlite_repository import SqliteIncidentRepository
from app.services.incident_service import IncidentService
from app.models.incident import CitizenReportCreate
from app.core.enums import BlockageSeverity

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

def test_task_creation_idempotency(service):
    report = CitizenReportCreate(
        reporter_name="Citizen A",
        ward_id="WARD-12",
        ward_name="Central Metro",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.SEVERE,
        description="Blocked main culvert"
    )
    inc = service.create_incident(report)
    service.analyze_risk(inc.id)
    service.prioritize_incident(inc.id)
    service.generate_recommendation(inc.id)
    service.submit_for_human_approval(inc.id)
    inc = service.review_human_approval(inc.id, approved=True, reviewer="Officer_X", rationale="Approved")

    first_task = inc.response_task
    assert first_task is not None
    first_task_id = first_task.task_id

    # Call create_response_task second and third time
    inc2 = service.create_response_task(inc.id)
    assert inc2.response_task.task_id == first_task_id

    inc3 = service.create_response_task(inc.id)
    assert inc3.response_task.task_id == first_task_id
