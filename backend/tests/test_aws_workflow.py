import pytest
from moto import mock_aws

from app.models.incident import CitizenReportCreate
from app.core.enums import IncidentStatus, BlockageSeverity
from app.db.dynamodb_repository import DynamoDbIncidentRepository
from app.services.s3_storage import S3StorageService
from app.services.incident_service import IncidentService

@pytest.fixture
def aws_workflow_env():
    with mock_aws():
        dynamo_repo = DynamoDbIncidentRepository(
            table_name="ProjectTable",
            region_name="ap-south-1"
        )
        dynamo_repo._ensure_table_exists()

        s3_svc = S3StorageService(
            bucket_name="project-evidence-a7k29x",
            region_name="ap-south-1"
        )
        s3_svc._ensure_bucket_exists()

        service = IncidentService(dynamo_repo)
        yield service, s3_svc

def test_full_aws_workflow_end_to_end(aws_workflow_env):
    service, s3_svc = aws_workflow_env

    # 1. Citizen submits report
    report = CitizenReportCreate(
        reporter_name="AWS Workflow Tester",
        reporter_phone="+91-99887-11223",
        ward_id="WARD-12",
        ward_name="Central Metro & Commercial Hub",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.COMPLETE,
        water_depth_cm=45.0,
        description="Massive blockage under highway flyover culvert.",
        landmark="Near Central Metro Pillar 10"
    )
    inc = service.create_incident(report)
    assert inc.status == IncidentStatus.NEW

    # 2. Verify stored in DynamoDB
    retrieved = service.repo.get(inc.id)
    assert retrieved is not None
    assert retrieved.id == inc.id

    # 3. Analyze Risk (Deterministic Engine)
    inc = service.analyze_risk(inc.id)
    assert inc.status == IncidentStatus.ANALYZING
    assert inc.risk_assessment is not None
    assert inc.risk_assessment.risk_score > 0

    # 4. Urgency Prioritization
    inc = service.prioritize_incident(inc.id)
    assert inc.status == IncidentStatus.PRIORITIZED
    assert inc.priority is not None

    # 5. Recommendation
    inc = service.generate_recommendation(inc.id)
    assert inc.status == IncidentStatus.RECOMMENDED

    # 6. Submit for Human Approval
    inc = service.submit_for_human_approval(inc.id)
    assert inc.status == IncidentStatus.AWAITING_APPROVAL

    # 7. Human Review & Approval (Creates Response Task via DynamoDB conditional write)
    inc = service.review_human_approval(
        incident_id=inc.id,
        approved=True,
        reviewer="Chief_Dispatcher_Kapoor",
        rationale="Critical arterial underpass at risk; authorized immediate Super-Sucker dispatch."
    )
    assert inc.status == IncidentStatus.IN_PROGRESS
    assert inc.response_task is not None
    assert "NOT occurred yet" in inc.response_task.disclaimer

    # 8. Duplicate Task Idempotency Check
    task_id_first = inc.response_task.task_id
    inc_dup = service.create_response_task(inc.id)
    assert inc_dup.response_task.task_id == task_id_first

    # 9. Upload S3 Evidence File
    evidence_res = s3_svc.upload_evidence(
        file_bytes=b"sample field camera photo of cleared silt",
        filename="post_suction_pipe.jpg",
        incident_id=inc.id,
        content_type="image/jpeg"
    )
    assert "evidence/" in evidence_res["s3_key"]

    # 10. Record Field Resolution with S3 Key reference
    inc = service.record_resolution(
        incident_id=inc.id,
        resolution_notes="Super-sucker removed 4 metric tons of sediment. Culvert pipe clear.",
        evidence_url=evidence_res["s3_key"]
    )
    assert inc.status == IncidentStatus.RESOLVED

    # 11. Telemetry Verification
    inc = service.verify_resolution(
        incident_id=inc.id,
        sensor_flow_rate_lps=80.0,
        post_clearance_depth_cm=0.0
    )
    assert inc.status == IncidentStatus.VERIFIED
    assert inc.verification.verified is True

    # 12. Final DynamoDB item verification
    final_db_item = service.repo.get(inc.id)
    assert final_db_item.status == IncidentStatus.VERIFIED
    assert len(final_db_item.audit_history) >= 7
    assert final_db_item.response_task.evidence_url == evidence_res["s3_key"]
