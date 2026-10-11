from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.incident import Incident, CitizenReportCreate
from app.services.incident_service import IncidentService
from app.core.exceptions import IncidentNotFoundError

router = APIRouter(prefix="/incidents", tags=["incidents"])
service = IncidentService()

@router.post("", response_model=Incident, status_code=201)
def submit_incident_report(report: CitizenReportCreate):
    """Step 1 & 2: Citizen submits waterlogging or blocked drain report."""
    return service.create_incident(report)

@router.get("", response_model=List[Incident])
def list_incidents(
    status: Optional[str] = Query(None, description="Filter by IncidentStatus"),
    ward_id: Optional[str] = Query(None, description="Filter by Ward ID"),
    active_only: bool = Query(False, description="Filter to non-terminal states")
):
    """Retrieves list of all reported incidents."""
    incidents = service.repo.find_active() if active_only else service.repo.list_all()
    if status:
        incidents = [i for i in incidents if i.status.value == status]
    if ward_id:
        incidents = [i for i in incidents if i.report.ward_id == ward_id]
    return incidents

@router.get("/{incident_id}", response_model=Incident)
def get_incident(incident_id: str):
    """Retrieves single incident details with risk breakdown, task, and verification."""
    try:
        return service._get_or_raise(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

@router.get("/{incident_id}/audit")
def get_incident_audit(incident_id: str):
    """Retrieves complete immutable activity and verification audit log for the incident."""
    try:
        inc = service._get_or_raise(incident_id)
        return {
            "incident_id": inc.id,
            "status": inc.status.value,
            "audit_history": inc.audit_history
        }
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

@router.post("/{incident_id}/archive")
def archive_incident(incident_id: str):
    """Archives verified/closed incident to S3 cold storage and purges from active database."""
    try:
        return service.archive_incident(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

