from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.models.incident import Incident
from app.services.incident_service import IncidentService
from app.agent.orchestrator import get_orchestrator
from app.core.exceptions import (
    IncidentNotFoundError,
    InvalidStateTransitionError,
    TaskAlreadyExistsError
)

router = APIRouter(prefix="/incidents", tags=["workflow"])
service = IncidentService()

class HumanApprovalRequest(BaseModel):
    approved: bool
    reviewer: str = Field("Supervisor_Dispatch", description="Name or ID of municipal officer")
    rationale: str = Field(..., min_length=3, description="Decision justification")

class ResolutionRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=5, description="Field crew completion notes")
    evidence_url: Optional[str] = Field(None, description="Photo or sensor evidence URL")

class VerificationRequest(BaseModel):
    sensor_flow_rate_lps: float = Field(75.0, description="Post-clearance culvert flow rate in L/s")
    post_clearance_depth_cm: float = Field(0.0, description="Residual water depth in cm")
    inspection_photo: Optional[str] = None
    simulate_failure: bool = Field(False, description="Simulate sensor anomaly or insufficient drainage")

@router.post("/{incident_id}/analyze", response_model=Incident)
def analyze_incident(incident_id: str):
    """Step 3 & 4: Calculates deterministic risk score and severity."""
    try:
        return service.analyze_risk(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{incident_id}/prioritize", response_model=Incident)
def prioritize_incident(incident_id: str):
    """Step 5: Prioritizes and ranks incident against active queue."""
    try:
        return service.prioritize_incident(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{incident_id}/recommend", response_model=Incident)
def recommend_incident_response(incident_id: str):
    """Step 6: Recommends response action plan and submits for supervisor approval."""
    try:
        inc = service.generate_recommendation(incident_id)
        return service.submit_for_human_approval(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{incident_id}/triage")
def run_agent_triage_pipeline(incident_id: str):
    """Executes the full automated Strands Agent tool pipeline on the incident."""
    try:
        orch = get_orchestrator()
        return orch.process_incident_end_to_end(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{incident_id}/approval", response_model=Incident)
def review_approval(incident_id: str, payload: HumanApprovalRequest):
    """Step 7 & 8: Human supervisor reviews proposed response; on approval, response task is created."""
    try:
        return service.review_human_approval(
            incident_id=incident_id,
            approved=payload.approved,
            reviewer=payload.reviewer,
            rationale=payload.rationale
        )
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{incident_id}/tasks", response_model=Incident)
def create_task(incident_id: str):
    """Step 8: Dispatches response task. Idempotent: duplicate calls return the existing task."""
    try:
        return service.create_response_task(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{incident_id}/resolve", response_model=Incident)
def record_resolution(incident_id: str, payload: ResolutionRequest):
    """Step 9: Records field resolution and clearance notes with evidence."""
    try:
        return service.record_resolution(
            incident_id=incident_id,
            resolution_notes=payload.resolution_notes,
            evidence_url=payload.evidence_url
        )
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{incident_id}/verify", response_model=Incident)
def verify_resolution(incident_id: str, payload: VerificationRequest):
    """Step 10: Verifies drainage telemetry. If telemetry fails, moves to NEEDS_HUMAN_REVIEW."""
    try:
        return service.verify_resolution(
            incident_id=incident_id,
            sensor_flow_rate_lps=payload.sensor_flow_rate_lps,
            post_clearance_depth_cm=payload.post_clearance_depth_cm,
            inspection_photo=payload.inspection_photo,
            simulate_failure=payload.simulate_failure
        )
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
