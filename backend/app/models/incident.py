from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid

from app.core.enums import IncidentStatus, BlockageSeverity, ActionType
from app.models.risk import RiskAssessment, PriorityScore

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class CitizenReportCreate(BaseModel):
    reporter_name: str = Field(..., min_length=2)
    reporter_phone: Optional[str] = None
    ward_id: str = Field(..., description="E.g., WARD-12, WARD-04")
    ward_name: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    drain_blockage_level: BlockageSeverity
    water_depth_cm: Optional[float] = Field(None, ge=0.0)
    description: str = Field(..., min_length=5)
    landmark: Optional[str] = None
    image_url: Optional[str] = None

class AuditLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=utc_now)
    actor: str = Field(..., description="E.g. citizen, risk_engine, strands_agent, human_dispatcher, field_crew, verification_system")
    action: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    reason: str = ""
    details: Dict[str, Any] = {}

class ResponseTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"TASK-{uuid.uuid4().hex[:8].upper()}")
    incident_id: str
    created_at: datetime = Field(default_factory=utc_now)
    action_type: ActionType
    assigned_unit: str
    priority: str
    status: str = "DISPATCHED"
    disclaimer: str = "Response dispatch order issued to Municipal Field Unit. Physical drainage clearance has NOT occurred yet."
    completed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    evidence_url: Optional[str] = None

class VerificationResult(BaseModel):
    verified: bool
    verified_at: datetime = Field(default_factory=utc_now)
    verified_by: str = "Automated Telemetry & Quality Inspection"
    simulated: bool = True
    sensor_flow_rate_lps: float = 0.0
    post_clearance_depth_cm: float = 0.0
    notes: str = ""
    evidence_matched: bool = True

class HumanApprovalDecision(BaseModel):
    approved: bool
    reviewer: str = "Supervisor_Dispatch"
    reviewed_at: datetime = Field(default_factory=utc_now)
    rationale: str
    action_plan_overridden: Optional[str] = None

class Incident(BaseModel):
    id: str = Field(default_factory=lambda: f"INC-{uuid.uuid4().hex[:8].upper()}")
    report: CitizenReportCreate
    status: IncidentStatus = IncidentStatus.NEW
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    risk_assessment: Optional[RiskAssessment] = None
    priority: Optional[PriorityScore] = None
    recommended_action: Optional[Dict[str, Any]] = None
    human_approval: Optional[HumanApprovalDecision] = None
    response_task: Optional[ResponseTask] = None
    verification: Optional[VerificationResult] = None
    audit_history: List[AuditLogEntry] = []
