import os
import tempfile
import pytest
import boto3
from moto import mock_aws

from app.models.incident import Incident, CitizenReportCreate, ResponseTask
from app.core.enums import IncidentStatus, BlockageSeverity, ActionType
from app.core.exceptions import InvalidStateTransitionError, TaskAlreadyExistsError, IncidentNotFoundError
from app.db.sqlite_repository import SqliteIncidentRepository
from app.db.dynamodb_repository import DynamoDbIncidentRepository

@pytest.fixture
def sqlite_repo():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    repo = SqliteIncidentRepository(path)
    yield repo
    try:
        os.remove(path)
    except Exception:
        pass

@pytest.fixture
def dynamodb_repo():
    with mock_aws():
        repo = DynamoDbIncidentRepository(
            table_name="contract-test-incidents",
            region_name="ap-south-1"
        )
        repo._ensure_table_exists()
        yield repo

@pytest.fixture(params=["sqlite", "dynamodb"])
def repo(request, sqlite_repo, dynamodb_repo):
    if request.param == "sqlite":
        return sqlite_repo
    else:
        return dynamodb_repo

def _sample_incident(incident_id="INC-CONTRACT-01", status=IncidentStatus.NEW):
    report = CitizenReportCreate(
        reporter_name="Contract Reporter",
        ward_id="WARD-12",
        ward_name="Central Metro",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.SEVERE,
        water_depth_cm=35.0,
        description="Drain blocked near underpass"
    )
    inc = Incident(id=incident_id, report=report, status=status)
    return inc

def test_contract_crud(repo):
    inc = _sample_incident("INC-CRUD-01")
    saved = repo.save(inc)
    assert saved.id == "INC-CRUD-01"

    fetched = repo.get("INC-CRUD-01")
    assert fetched is not None
    assert fetched.id == "INC-CRUD-01"
    assert fetched.report.ward_name == "Central Metro"

    deleted = repo.delete("INC-CRUD-01")
    assert deleted is True

    assert repo.get("INC-CRUD-01") is None

def test_contract_find_active(repo):
    inc1 = _sample_incident("INC-ACTIVE-01", status=IncidentStatus.NEW)
    inc2 = _sample_incident("INC-ACTIVE-02", status=IncidentStatus.IN_PROGRESS)
    inc3 = _sample_incident("INC-RESOLVED-03", status=IncidentStatus.RESOLVED)
    inc4 = _sample_incident("INC-VERIFIED-04", status=IncidentStatus.VERIFIED)
    inc5 = _sample_incident("INC-REJECTED-05", status=IncidentStatus.REJECTED)

    for i in [inc1, inc2, inc3, inc4, inc5]:
        repo.save(i)

    active = repo.find_active()
    active_ids = [a.id for a in active]

    assert "INC-ACTIVE-01" in active_ids
    assert "INC-ACTIVE-02" in active_ids
    assert "INC-RESOLVED-03" not in active_ids
    assert "INC-VERIFIED-04" not in active_ids
    assert "INC-REJECTED-05" not in active_ids

def test_contract_save_transition_success_and_failure(repo):
    inc = _sample_incident("INC-TRANS-01", status=IncidentStatus.NEW)
    repo.save(inc)

    # Valid transition from NEW to ANALYZING
    inc.status = IncidentStatus.ANALYZING
    updated = repo.save_transition(inc, expected_current_status=IncidentStatus.NEW)
    assert updated.status == IncidentStatus.ANALYZING

    # Attempt transition from wrong expected status (expects NEW, but current is ANALYZING)
    inc.status = IncidentStatus.PRIORITIZED
    with pytest.raises(InvalidStateTransitionError):
        repo.save_transition(inc, expected_current_status=IncidentStatus.NEW)

def test_contract_save_task_dispatch_idempotency(repo):
    inc = _sample_incident("INC-DISP-01", status=IncidentStatus.APPROVED)
    repo.save(inc)

    # First dispatch succeeds
    inc.response_task = ResponseTask(
        incident_id=inc.id,
        action_type=ActionType.DISPATCH_SUPER_SUCKER,
        assigned_unit="Sector 12 Unit",
        priority="CRITICAL"
    )
    first_saved = repo.save_task_dispatch(inc)
    assert first_saved.response_task is not None

    # Second dispatch raises TaskAlreadyExistsError
    with pytest.raises(TaskAlreadyExistsError):
        repo.save_task_dispatch(inc)
