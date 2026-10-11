import pytest
import boto3
from moto import mock_aws
from datetime import datetime, timezone

from app.models.incident import Incident, CitizenReportCreate, AuditLogEntry, ResponseTask
from app.models.risk import RiskAssessment, RiskFactorBreakdown
from app.core.enums import IncidentStatus, BlockageSeverity, Severity, ActionType
from app.core.exceptions import InvalidStateTransitionError, TaskAlreadyExistsError
from app.db.dynamodb_repository import DynamoDbIncidentRepository

@pytest.fixture
def dynamodb_env():
    with mock_aws():
        repo = DynamoDbIncidentRepository(
            table_name="monsoon-sentinel-incidents",
            region_name="ap-south-1"
        )
        repo._ensure_table_exists()
        yield repo

def test_dynamodb_key_schema_and_item_structure(dynamodb_env):
    repo = dynamodb_env
    # Verify table key schema has pk (HASH) and sk (RANGE)
    table_desc = repo._table.meta.client.describe_table(TableName="monsoon-sentinel-incidents")
    key_schema = {k["AttributeName"]: k["KeyType"] for k in table_desc["Table"]["KeySchema"]}
    assert key_schema.get("pk") == "HASH"
    assert key_schema.get("sk") == "RANGE"

    report = CitizenReportCreate(
        reporter_name="Schema Tester",
        reporter_phone="+91-98765-00000",
        ward_id="WARD-12",
        ward_name="Central Metro",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.SEVERE,
        water_depth_cm=25.0,
        description="Drain blocked at junction"
    )
    inc = Incident(id="INC-SCHEMA-01", report=report, status=IncidentStatus.NEW)
    repo.save(inc)

    # Directly inspect raw DynamoDB item
    raw = repo._table.get_item(Key={"pk": "INCIDENT#INC-SCHEMA-01", "sk": "METADATA"})
    assert "Item" in raw
    item = raw["Item"]
    assert item["pk"] == "INCIDENT#INC-SCHEMA-01"
    assert item["sk"] == "METADATA"
    assert item["incident_id"] == "INC-SCHEMA-01"
    assert item["status"] == "NEW"

def test_dynamodb_full_incident_persistence(dynamodb_env):
    repo = dynamodb_env

    report = CitizenReportCreate(
        reporter_name="Sunil Mehta",
        reporter_phone="+91-98765-11223",
        ward_id="WARD-12",
        ward_name="Central Metro",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.COMPLETE,
        water_depth_cm=50.0,
        description="Water submerged traffic intersection near metro pillar",
        landmark="Metro Pillar 144"
    )

    incident = Incident(id="INC-DDB-001", report=report, status=IncidentStatus.ANALYZING)
    incident.risk_assessment = RiskAssessment(
        incident_id=incident.id,
        risk_score=85.0,
        severity=Severity.CRITICAL,
        factors=[
            RiskFactorBreakdown(
                factor_name="Rainfall Intensity",
                raw_value=42.5,
                normalized_score=85.0,
                weight=0.35,
                contribution=29.75
            )
        ],
        explanation="Deterministic critical risk"
    )
    incident.audit_history.append(AuditLogEntry(
        actor="risk_engine",
        action="CALCULATE_RISK_SCORE",
        reason="Deterministic score: 85.0"
    ))

    # Save to DynamoDB
    saved = repo.save(incident)
    assert saved.id == "INC-DDB-001"

    # Fetch from DynamoDB
    retrieved = repo.get("INC-DDB-001")
    assert retrieved is not None
    assert retrieved.id == "INC-DDB-001"
    assert retrieved.status == IncidentStatus.ANALYZING
    assert retrieved.risk_assessment.risk_score == 85.0
    assert retrieved.risk_assessment.severity == Severity.CRITICAL
    assert len(retrieved.audit_history) == 1
    assert retrieved.audit_history[0].actor == "risk_engine"

def test_dynamodb_persistence_across_restarts(dynamodb_env):
    """Simulates application restart by dropping the repository object and initializing a new instance."""
    repo1 = dynamodb_env

    report = CitizenReportCreate(
        reporter_name="Restart Test",
        ward_id="WARD-04",
        ward_name="North Industrial",
        latitude=13.0358,
        longitude=77.5970,
        drain_blockage_level=BlockageSeverity.SEVERE,
        description="Drain clogged with factory silt"
    )
    inc = Incident(id="INC-RESTART-99", report=report, status=IncidentStatus.NEW)
    repo1.save(inc)

    # Simulate restart by creating repo2 pointing to same DynamoDB table
    repo2 = DynamoDbIncidentRepository(
        table_name="monsoon-sentinel-incidents",
        region_name="ap-south-1"
    )

    fetched = repo2.get("INC-RESTART-99")
    assert fetched is not None
    assert fetched.id == "INC-RESTART-99"
    assert fetched.report.reporter_name == "Restart Test"
    assert fetched.status == IncidentStatus.NEW

def test_dynamodb_conditional_state_transitions(dynamodb_env):
    repo = dynamodb_env

    report = CitizenReportCreate(
        reporter_name="Transition Tester",
        ward_id="WARD-12",
        ward_name="Central Metro",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.PARTIAL,
        description="Pooling water"
    )
    inc = Incident(id="INC-TRANS-DDB", report=report, status=IncidentStatus.NEW)
    repo.save(inc)

    # Valid conditional transition
    inc.status = IncidentStatus.ANALYZING
    repo.save_transition(inc, expected_current_status=IncidentStatus.NEW)
    assert repo.get("INC-TRANS-DDB").status == IncidentStatus.ANALYZING

    # Invalid conditional transition: expects NEW, but table has ANALYZING
    inc.status = IncidentStatus.PRIORITIZED
    with pytest.raises(InvalidStateTransitionError):
        repo.save_transition(inc, expected_current_status=IncidentStatus.NEW)

def test_dynamodb_duplicate_task_prevention(dynamodb_env):
    repo = dynamodb_env

    report = CitizenReportCreate(
        reporter_name="Task Tester",
        ward_id="WARD-07",
        ward_name="South Lakeside",
        latitude=12.9352,
        longitude=77.6245,
        drain_blockage_level=BlockageSeverity.SEVERE,
        description="Lakeside overflow"
    )
    inc = Incident(id="INC-TASK-DDB", report=report, status=IncidentStatus.APPROVED)
    repo.save(inc)

    # First dispatch
    inc.response_task = ResponseTask(
        incident_id=inc.id,
        action_type=ActionType.DEPLOY_DEWATERING_PUMP,
        assigned_unit="Lakeside Unit 1",
        priority="HIGH"
    )
    repo.save_task_dispatch(inc)

    # Second dispatch attempted
    with pytest.raises(TaskAlreadyExistsError):
        repo.save_task_dispatch(inc)
