from fastapi import APIRouter
from app.db.sqlite_repository import get_repository
from app.core.enums import IncidentStatus, Severity

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("")
def get_dashboard_statistics():
    """Derives dynamic operational statistics directly from current repository state.
    Never hardcoded.
    """
    repo = get_repository()
    all_incidents = repo.list_all()

    total_incidents = len(all_incidents)
    active_incidents = len([i for i in all_incidents if i.status not in [
        IncidentStatus.RESOLVED,
        IncidentStatus.VERIFIED,
        IncidentStatus.REJECTED,
        IncidentStatus.CANCELLED
    ]])

    awaiting_approval = len([i for i in all_incidents if i.status == IncidentStatus.AWAITING_APPROVAL])
    in_progress = len([i for i in all_incidents if i.status == IncidentStatus.IN_PROGRESS])
    resolved_count = len([i for i in all_incidents if i.status == IncidentStatus.RESOLVED])
    verified_count = len([i for i in all_incidents if i.status == IncidentStatus.VERIFIED])
    needs_review = len([i for i in all_incidents if i.status == IncidentStatus.NEEDS_HUMAN_REVIEW])
    rejected_count = len([i for i in all_incidents if i.status == IncidentStatus.REJECTED])

    # Severity distribution
    severity_counts = {
        Severity.CRITICAL.value: 0,
        Severity.HIGH.value: 0,
        Severity.MEDIUM.value: 0,
        Severity.LOW.value: 0,
        "UNASSESSED": 0
    }

    total_water_depth = 0.0
    depth_samples = 0

    for inc in all_incidents:
        if inc.risk_assessment:
            sev_key = inc.risk_assessment.severity.value
            severity_counts[sev_key] = severity_counts.get(sev_key, 0) + 1
        else:
            severity_counts["UNASSESSED"] += 1

        if inc.report.water_depth_cm is not None:
            total_water_depth += inc.report.water_depth_cm
            depth_samples += 1

    avg_water_depth_cm = round(total_water_depth / depth_samples, 1) if depth_samples > 0 else 0.0

    return {
        "total_incidents": total_incidents,
        "active_incidents": active_incidents,
        "awaiting_approval": awaiting_approval,
        "in_progress": in_progress,
        "resolved": resolved_count,
        "verified": verified_count,
        "needs_human_review": needs_review,
        "rejected": rejected_count,
        "severity_breakdown": severity_counts,
        "average_reported_depth_cm": avg_water_depth_cm,
        "data_mode": "SIMULATED_LOCAL_MVP",
        "mock_sagemaker_active": True
    }
