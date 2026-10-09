from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.core.enums import IncidentStatus, ActionType, Severity
from app.core.exceptions import (
    IncidentNotFoundError,
    InvalidStateTransitionError,
    TaskAlreadyExistsError,
    VerificationFailedError
)
from app.models.incident import (
    Incident,
    CitizenReportCreate,
    AuditLogEntry,
    ResponseTask,
    HumanApprovalDecision,
    VerificationResult
)
from app.models.risk import RiskAssessment, PriorityScore
from app.db.base_repository import IncidentRepositoryBase
from app.db.sqlite_repository import get_repository
from app.services.risk_engine import RiskEngine
from app.services.prioritization import PrioritizationService

class IncidentService:
    """Manages the end-to-end incident lifecycle, state transitions,
    deterministic risk calculations, and audit history.
    """

    VALID_TRANSITIONS: Dict[IncidentStatus, List[IncidentStatus]] = {
        IncidentStatus.NEW: [IncidentStatus.ANALYZING, IncidentStatus.CANCELLED],
        IncidentStatus.ANALYZING: [IncidentStatus.PRIORITIZED, IncidentStatus.CANCELLED],
        IncidentStatus.PRIORITIZED: [IncidentStatus.RECOMMENDED, IncidentStatus.CANCELLED],
        IncidentStatus.RECOMMENDED: [IncidentStatus.AWAITING_APPROVAL, IncidentStatus.CANCELLED],
        IncidentStatus.AWAITING_APPROVAL: [IncidentStatus.APPROVED, IncidentStatus.REJECTED, IncidentStatus.CANCELLED],
        IncidentStatus.APPROVED: [IncidentStatus.IN_PROGRESS],
        IncidentStatus.IN_PROGRESS: [IncidentStatus.RESOLVED],
        IncidentStatus.RESOLVED: [IncidentStatus.VERIFIED, IncidentStatus.NEEDS_HUMAN_REVIEW],
        IncidentStatus.NEEDS_HUMAN_REVIEW: [IncidentStatus.IN_PROGRESS, IncidentStatus.CANCELLED],
        IncidentStatus.REJECTED: [],
        IncidentStatus.CANCELLED: [],
        IncidentStatus.VERIFIED: [],
    }

    def __init__(self, repository: Optional[IncidentRepositoryBase] = None):
        self._repo = repository

    @property
    def repo(self) -> IncidentRepositoryBase:
        if self._repo is not None:
            return self._repo
        return get_repository()

    def _get_or_raise(self, incident_id: str) -> Incident:
        inc = self.repo.get(incident_id)
        if not inc:
            raise IncidentNotFoundError(incident_id)
        return inc

    def create_incident(self, report: CitizenReportCreate) -> Incident:
        """Step 1 & 2: Citizen submits report, validated and stored."""
        incident = Incident(report=report, status=IncidentStatus.NEW)
        audit_entry = AuditLogEntry(
            actor="citizen",
            action="SUBMIT_REPORT",
            from_status=None,
            to_status=IncidentStatus.NEW.value,
            reason=f"Citizen {report.reporter_name} reported waterlogging in {report.ward_name}",
            details={"description": report.description, "ward_id": report.ward_id}
        )
        incident.audit_history.append(audit_entry)
        self.repo.save(incident)
        return incident

    def transition_state(
        self,
        incident: Incident,
        new_status: IncidentStatus,
        actor: str,
        action: str,
        reason: str = "",
        details: Optional[Dict[str, Any]] = None
    ) -> Incident:
        allowed = self.VALID_TRANSITIONS.get(incident.status, [])
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                current_status=incident.status.value,
                target_status=new_status.value,
                reason=f"Valid next states are: {[s.value for s in allowed]}"
            )

        old_status = incident.status
        incident.status = new_status
        incident.updated_at = datetime.now(timezone.utc)

        audit_entry = AuditLogEntry(
            actor=actor,
            action=action,
            from_status=old_status.value,
            to_status=new_status.value,
            reason=reason,
            details=details or {}
        )
        incident.audit_history.append(audit_entry)
        return self.repo.save_transition(incident, expected_current_status=old_status)

    def analyze_risk(self, incident_id: str) -> Incident:
        """Step 3 & 4: Retrieve environmental data & compute deterministic risk score."""
        incident = self._get_or_raise(incident_id)
        if incident.status == IncidentStatus.NEW:
            incident = self.transition_state(
                incident, IncidentStatus.ANALYZING,
                actor="risk_engine",
                action="BEGIN_ANALYSIS",
                reason="Environmental telemetry and spatial correlation analysis started."
            )

        active_incidents = self.repo.find_active()
        assessment = RiskEngine.calculate_risk(incident, nearby_incidents=active_incidents)
        incident.risk_assessment = assessment

        # Log risk calculation in audit
        incident.audit_history.append(AuditLogEntry(
            actor="risk_engine",
            action="CALCULATE_RISK_SCORE",
            from_status=incident.status.value,
            to_status=incident.status.value,
            reason=f"Deterministic score: {assessment.risk_score} ({assessment.severity.value})",
            details={
                "risk_score": assessment.risk_score,
                "severity": assessment.severity.value,
                "missing_factors": assessment.missing_factors,
                "uncertainty_penalty": assessment.uncertainty_penalty
            }
        ))
        self.repo.save(incident)
        return incident

    def prioritize_incident(self, incident_id: str) -> Incident:
        """Step 5: Prioritization service ranks incident."""
        incident = self._get_or_raise(incident_id)
        if not incident.risk_assessment:
            incident = self.analyze_risk(incident_id)

        all_active = self.repo.find_active()
        priority = PrioritizationService.prioritize_single(incident, all_active)
        incident.priority = priority

        if incident.status == IncidentStatus.ANALYZING:
            incident = self.transition_state(
                incident, IncidentStatus.PRIORITIZED,
                actor="prioritization_service",
                action="SET_PRIORITY",
                reason=f"Urgency score: {priority.urgency_score}, Rank: #{priority.priority_rank}",
                details={"urgency": priority.urgency_score, "rank": priority.priority_rank}
            )
        else:
            self.repo.save(incident)

        return incident

    def generate_recommendation(self, incident_id: str, suggested_action: Optional[Dict[str, Any]] = None) -> Incident:
        """Step 6: Agent/System recommends response action."""
        incident = self._get_or_raise(incident_id)
        if incident.status == IncidentStatus.ANALYZING:
            incident = self.prioritize_incident(incident_id)

        # Deterministic default recommendation based on severity and blockage
        sev = incident.risk_assessment.severity if incident.risk_assessment else Severity.MEDIUM
        blockage = incident.report.drain_blockage_level

        if sev == Severity.CRITICAL:
            action_type = ActionType.DISPATCH_SUPER_SUCKER.value
            equipment = "High-pressure Super-Sucker Hydro-Vacuum Rig & Dewatering Crew"
            estimated_duration_min = 45
        elif sev == Severity.HIGH:
            action_type = ActionType.DEPLOY_DEWATERING_PUMP.value
            equipment = "150 GPM Mobile Dewatering Pump & Drain Snake Crew"
            estimated_duration_min = 60
        elif blockage.value in ["SEVERE", "COMPLETE"]:
            action_type = ActionType.MANUAL_DESILTING_CREW.value
            equipment = "Emergency Desilting Task Force (4 Personnel)"
            estimated_duration_min = 90
        else:
            action_type = ActionType.INSPECT_CULVERT.value
            equipment = "Rapid Drain Assessment & Trash-Rack Clearance Unit"
            estimated_duration_min = 30

        recommendation = suggested_action or {
            "action_type": action_type,
            "equipment": equipment,
            "assigned_unit": f"Municipal Rapid Response Division - Sector {incident.report.ward_id}",
            "priority": sev.value,
            "estimated_duration_min": estimated_duration_min,
            "rationale": f"Calculated severity is {sev.value} with {blockage.value} blockage. Immediate drainage clearance required.",
            "requires_human_approval": True,
            "disclaimer": "Physical drain clearance will only commence after supervisor review and crew deployment."
        }
        incident.recommended_action = recommendation

        if incident.status == IncidentStatus.PRIORITIZED:
            incident = self.transition_state(
                incident, IncidentStatus.RECOMMENDED,
                actor="strands_agent",
                action="RECOMMEND_RESPONSE",
                reason=f"Recommended {action_type} based on risk score.",
                details=recommendation
            )
        else:
            self.repo.save(incident)

        return incident

    def submit_for_human_approval(self, incident_id: str, reason: str = "") -> Incident:
        incident = self._get_or_raise(incident_id)
        if incident.status == IncidentStatus.RECOMMENDED:
            incident = self.transition_state(
                incident, IncidentStatus.AWAITING_APPROVAL,
                actor="strands_agent",
                action="REQUEST_HUMAN_APPROVAL",
                reason=reason or "Response plan submitted to Municipal Supervisor for formal authorization."
            )
        return incident

    def review_human_approval(
        self,
        incident_id: str,
        approved: bool,
        reviewer: str,
        rationale: str
    ) -> Incident:
        """Step 7: Human supervisor approves or rejects proposed response."""
        incident = self._get_or_raise(incident_id)
        if incident.status != IncidentStatus.AWAITING_APPROVAL:
            raise InvalidStateTransitionError(
                incident.status.value,
                IncidentStatus.APPROVED.value if approved else IncidentStatus.REJECTED.value,
                "Incident must be in AWAITING_APPROVAL status."
            )

        incident.human_approval = HumanApprovalDecision(
            approved=approved,
            reviewer=reviewer,
            reviewed_at=datetime.now(timezone.utc),
            rationale=rationale
        )

        if approved:
            incident = self.transition_state(
                incident, IncidentStatus.APPROVED,
                actor=f"human_supervisor ({reviewer})",
                action="APPROVE_RESPONSE",
                reason=f"Authorized action plan. Rationale: {rationale}"
            )
            # Step 8: Create response task upon approval
            incident = self.create_response_task(incident_id)
        else:
            incident = self.transition_state(
                incident, IncidentStatus.REJECTED,
                actor=f"human_supervisor ({reviewer})",
                action="REJECT_RESPONSE",
                reason=f"Rejected action plan. Rationale: {rationale}"
            )

        return incident

    def create_response_task(
        self,
        incident_id: str,
        action_type_override: Optional[ActionType] = None,
        assigned_unit_override: Optional[str] = None,
        priority_override: Optional[str] = None
    ) -> Incident:
        """Step 8: Creates response task with strict idempotency (no duplicates)."""
        incident = self._get_or_raise(incident_id)

        # Idempotency check: if task already exists and is active, return without creating duplicate
        if incident.response_task is not None:
            # Idempotent return
            return incident

        rec = incident.recommended_action or {}
        raw_action = action_type_override.value if action_type_override else rec.get("action_type", ActionType.DEPLOY_DEWATERING_PUMP.value)
        action_type_enum = ActionType(raw_action) if raw_action in [a.value for a in ActionType] else ActionType.DEPLOY_DEWATERING_PUMP

        task = ResponseTask(
            incident_id=incident.id,
            created_at=datetime.now(timezone.utc),
            action_type=action_type_enum,
            assigned_unit=assigned_unit_override or rec.get("assigned_unit", "Municipal Rapid Response Division"),
            priority=priority_override or rec.get("priority", "HIGH"),
            status="DISPATCHED",
            disclaimer="Response dispatch order issued to Municipal Field Unit. Physical drainage clearance has NOT occurred yet."
        )
        incident.response_task = task

        if incident.status == IncidentStatus.APPROVED:
            incident = self.transition_state(
                incident, IncidentStatus.IN_PROGRESS,
                actor="dispatch_system",
                action="DISPATCH_TASK",
                reason=f"Field crew dispatched: {task.assigned_unit}. Note: Physical clearance is ongoing.",
                details={"task_id": task.task_id, "action_type": task.action_type.value}
            )
        else:
            try:
                incident = self.repo.save_task_dispatch(incident)
            except TaskAlreadyExistsError:
                return self._get_or_raise(incident_id)

        return incident

    def record_resolution(
        self,
        incident_id: str,
        resolution_notes: str,
        evidence_url: Optional[str] = None
    ) -> Incident:
        """Step 9: Accepts resolution update with field evidence."""
        incident = self._get_or_raise(incident_id)
        if incident.status not in [IncidentStatus.IN_PROGRESS, IncidentStatus.APPROVED]:
            raise InvalidStateTransitionError(
                incident.status.value,
                IncidentStatus.RESOLVED.value,
                "Resolution can only be submitted for in-progress tasks."
            )

        if incident.response_task:
            incident.response_task.status = "COMPLETED"
            incident.response_task.completed_at = datetime.now(timezone.utc)
            incident.response_task.resolution_notes = resolution_notes
            incident.response_task.evidence_url = evidence_url

        incident = self.transition_state(
            incident, IncidentStatus.RESOLVED,
            actor="field_crew",
            action="RECORD_RESOLUTION",
            reason=resolution_notes,
            details={"evidence_url": evidence_url, "notes": resolution_notes}
        )
        return incident

    def verify_resolution(
        self,
        incident_id: str,
        sensor_flow_rate_lps: float = 75.0,
        post_clearance_depth_cm: float = 0.0,
        inspection_photo: Optional[str] = None,
        simulate_failure: bool = False
    ) -> Incident:
        """Step 10: Verifies resolution.
        If verification succeeds -> VERIFIED.
        If verification fails -> transitions to NEEDS_HUMAN_REVIEW.
        """
        incident = self._get_or_raise(incident_id)
        if incident.status != IncidentStatus.RESOLVED:
            raise InvalidStateTransitionError(
                incident.status.value,
                IncidentStatus.VERIFIED.value,
                "Incident must be in RESOLVED state before verification."
            )

        # Verification logic: water depth must be receded (< 5 cm) and flow rate restored (> 20 LPS)
        passed = (not simulate_failure) and (post_clearance_depth_cm < 5.0) and (sensor_flow_rate_lps >= 20.0)

        verification = VerificationResult(
            verified=passed,
            verified_at=datetime.now(timezone.utc),
            verified_by="Municipal IoT Culvert Telemetry & Quality Assurance",
            simulated=True,
            sensor_flow_rate_lps=sensor_flow_rate_lps,
            post_clearance_depth_cm=post_clearance_depth_cm,
            notes="Water level cleared below safety threshold and drain flow restored to normal velocity." if passed else "Warning: Telemetry indicates persistent pooling or restricted culvert discharge.",
            evidence_matched=passed
        )
        incident.verification = verification

        if passed:
            incident = self.transition_state(
                incident, IncidentStatus.VERIFIED,
                actor="verification_service",
                action="VERIFY_RESOLUTION_SUCCESS",
                reason=f"Telemetry verified: Flow rate {sensor_flow_rate_lps} L/s, Depth {post_clearance_depth_cm} cm.",
                details={"verified": True, "flow_rate": sensor_flow_rate_lps, "depth_cm": post_clearance_depth_cm}
            )
        else:
            incident = self.transition_state(
                incident, IncidentStatus.NEEDS_HUMAN_REVIEW,
                actor="verification_service",
                action="VERIFY_RESOLUTION_FAILURE",
                reason=f"Verification failed: Residual depth {post_clearance_depth_cm} cm. Flagged for secondary inspection.",
                details={"verified": False, "flow_rate": sensor_flow_rate_lps, "depth_cm": post_clearance_depth_cm}
            )

        return incident
