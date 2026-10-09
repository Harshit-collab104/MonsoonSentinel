from typing import Dict, Any, Optional
import json
from strands import tool

from app.services.environmental import EnvironmentalDataService
from app.services.incident_service import IncidentService
from app.core.enums import ActionType

# Shared service instance
_incident_service = IncidentService()

def get_service() -> IncidentService:
    return _incident_service

@tool
def get_rainfall_forecast(latitude: float, longitude: float, ward_id: str = "WARD-12") -> str:
    """Retrieves current rainfall intensity (mm/h) and 2-hour forecast from municipal rain gauges."""
    data = EnvironmentalDataService.get_rainfall_forecast(latitude, longitude, ward_id)
    return json.dumps(data)

@tool
def get_historical_waterlogging(ward_id: str, location_id: str = "") -> str:
    """Retrieves historical flood frequency, chronic hotspot status, and records for a ward."""
    data = EnvironmentalDataService.get_historical_waterlogging(ward_id, location_id)
    return json.dumps(data)

@tool
def get_nearby_incidents(latitude: float, longitude: float, radius_km: float = 2.0) -> str:
    """Finds active waterlogging reports within a specified geographic radius."""
    svc = get_service()
    active = svc.repo.find_active()
    matches = []
    for inc in active:
        dist = EnvironmentalDataService.haversine_distance_km(
            latitude, longitude, inc.report.latitude, inc.report.longitude
        )
        if dist <= radius_km:
            matches.append({
                "incident_id": inc.id,
                "ward": inc.report.ward_name,
                "status": inc.status.value,
                "distance_km": round(dist, 2),
                "severity": inc.risk_assessment.severity.value if inc.risk_assessment else "UNKNOWN"
            })
    return json.dumps({"count": len(matches), "radius_km": radius_km, "nearby_incidents": matches})

@tool
def get_drainage_status(ward_id: str, drain_id: str = "") -> str:
    """Checks drainage network capacity (cusecs) and structural inspection status."""
    data = EnvironmentalDataService.get_drainage_status(ward_id, drain_id)
    return json.dumps(data)

@tool
def calculate_waterlogging_risk(incident_id: str) -> str:
    """Triggers deterministic risk calculation for an incident using sensor telemetry and spatial data."""
    svc = get_service()
    inc = svc.analyze_risk(incident_id)
    return json.dumps({
        "incident_id": inc.id,
        "risk_score": inc.risk_assessment.risk_score,
        "severity": inc.risk_assessment.severity.value,
        "missing_factors": inc.risk_assessment.missing_factors,
        "explanation": inc.risk_assessment.explanation
    })

@tool
def prioritize_incident(incident_id: str) -> str:
    """Ranks an incident by operational urgency relative to all active incidents."""
    svc = get_service()
    inc = svc.prioritize_incident(incident_id)
    return json.dumps({
        "incident_id": inc.id,
        "priority_rank": inc.priority.priority_rank if inc.priority else 1,
        "urgency_score": inc.priority.urgency_score if inc.priority else 0.0,
        "summary": inc.priority.recommendation_summary if inc.priority else ""
    })

@tool
def recommend_response(incident_id: str) -> str:
    """Recommends an operational action plan and equipment based on severity and blockage degree."""
    svc = get_service()
    inc = svc.generate_recommendation(incident_id)
    return json.dumps({
        "incident_id": inc.id,
        "recommended_action": inc.recommended_action,
        "status": inc.status.value
    })

@tool
def request_human_approval(incident_id: str, reason: str = "") -> str:
    """Submits the proposed response action plan to municipal supervisor for authorization."""
    svc = get_service()
    inc = svc.submit_for_human_approval(incident_id, reason)
    return json.dumps({
        "incident_id": inc.id,
        "status": inc.status.value,
        "awaiting_approval": True,
        "note": "Awaiting supervisor sign-off before dispatching physical equipment."
    })

@tool
def create_response_task(
    incident_id: str,
    action_type: str = "",
    assigned_unit: str = "",
    priority: str = ""
) -> str:
    """Dispatches a response task. Idempotent: returns existing task if already active. Does NOT claim drain is cleared."""
    svc = get_service()
    act = ActionType(action_type) if action_type in [a.value for a in ActionType] else None
    inc = svc.create_response_task(
        incident_id,
        action_type_override=act,
        assigned_unit_override=assigned_unit or None,
        priority_override=priority or None
    )
    task = inc.response_task
    return json.dumps({
        "incident_id": inc.id,
        "task_id": task.task_id if task else None,
        "status": task.status if task else None,
        "action_type": task.action_type.value if task else None,
        "disclaimer": task.disclaimer if task else ""
    })

@tool
def record_resolution(incident_id: str, resolution_notes: str, evidence_url: str = "") -> str:
    """Records completion notes and evidence from field team upon dewatering/clearance."""
    svc = get_service()
    inc = svc.record_resolution(incident_id, resolution_notes, evidence_url)
    return json.dumps({
        "incident_id": inc.id,
        "status": inc.status.value,
        "resolution_recorded": True
    })

@tool
def verify_resolution(
    incident_id: str,
    sensor_flow_rate_lps: float = 75.0,
    post_clearance_depth_cm: float = 0.0,
    simulate_failure: bool = False
) -> str:
    """Verifies drainage clearance via telemetry. Transitions to VERIFIED or NEEDS_HUMAN_REVIEW."""
    svc = get_service()
    inc = svc.verify_resolution(
        incident_id,
        sensor_flow_rate_lps=sensor_flow_rate_lps,
        post_clearance_depth_cm=post_clearance_depth_cm,
        simulate_failure=simulate_failure
    )
    return json.dumps({
        "incident_id": inc.id,
        "status": inc.status.value,
        "verified": inc.verification.verified if inc.verification else False,
        "telemetry_notes": inc.verification.notes if inc.verification else ""
    })

@tool
def get_incident_status(incident_id: str) -> str:
    """Fetches the complete status, risk score, task, and lifecycle state of an incident."""
    svc = get_service()
    inc = svc.repo.get(incident_id)
    if not inc:
        return json.dumps({"error": f"Incident {incident_id} not found."})
    return json.dumps({
        "incident_id": inc.id,
        "status": inc.status.value,
        "risk_score": inc.risk_assessment.risk_score if inc.risk_assessment else None,
        "severity": inc.risk_assessment.severity.value if inc.risk_assessment else None,
        "task": inc.response_task.model_dump() if inc.response_task else None,
        "verification": inc.verification.model_dump() if inc.verification else None,
        "audit_count": len(inc.audit_history)
    })

ALL_TOOLS = [
    get_rainfall_forecast,
    get_historical_waterlogging,
    get_nearby_incidents,
    get_drainage_status,
    calculate_waterlogging_risk,
    prioritize_incident,
    recommend_response,
    request_human_approval,
    create_response_task,
    record_resolution,
    verify_resolution,
    get_incident_status,
]
