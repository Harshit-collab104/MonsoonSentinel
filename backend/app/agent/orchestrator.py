from typing import Dict, Any, Optional, List
import json
from datetime import datetime, timezone

from app.agent.tools import (
    ALL_TOOLS,
    get_rainfall_forecast,
    get_historical_waterlogging,
    get_drainage_status,
    calculate_waterlogging_risk,
    prioritize_incident,
    recommend_response,
    request_human_approval,
    get_incident_status,
    get_service
)
from app.agent.sagemaker_adapter import SageMakerInferenceAdapter

class MonsoonAgentOrchestrator:
    """Orchestrates Strands Agent tools and SageMaker AI inference adapter
    for automated triage, risk assessment, and response recommendation.
    """

    def __init__(self):
        self.adapter = SageMakerInferenceAdapter()
        self.service = get_service()

    def process_incident_end_to_end(self, incident_id: str) -> Dict[str, Any]:
        """Runs the automated municipal triage pipeline through Strands tools:
        1. Telemetry & historical analysis
        2. Deterministic risk calculation
        3. Multi-incident prioritization
        4. Response recommendation
        5. Submit for human approval
        """
        tool_traces: List[Dict[str, Any]] = []
        actions_taken: List[str] = []

        # 1. Inspect status
        st_res = json.loads(get_incident_status(incident_id))
        tool_traces.append({"tool": "get_incident_status", "result": st_res, "timestamp": datetime.now(timezone.utc).isoformat()})
        actions_taken.append(f"Retrieved incident baseline status ({st_res.get('status')})")

        # 2. Risk Calculation
        risk_res = json.loads(calculate_waterlogging_risk(incident_id))
        tool_traces.append({"tool": "calculate_waterlogging_risk", "result": risk_res, "timestamp": datetime.now(timezone.utc).isoformat()})
        actions_taken.append(f"Calculated deterministic risk score: {risk_res.get('risk_score')}/100 ({risk_res.get('severity')})")

        # 3. Prioritization
        prio_res = json.loads(prioritize_incident(incident_id))
        tool_traces.append({"tool": "prioritize_incident", "result": prio_res, "timestamp": datetime.now(timezone.utc).isoformat()})
        actions_taken.append(f"Prioritized incident at rank #{prio_res.get('priority_rank', 1)} in municipal queue")

        # 4. Recommendation
        rec_res = json.loads(recommend_response(incident_id))
        tool_traces.append({"tool": "recommend_response", "result": rec_res, "timestamp": datetime.now(timezone.utc).isoformat()})
        recommended_action_type = rec_res.get("recommended_action", {}).get("action_type", "DEPLOY_DEWATERING_PUMP")
        actions_taken.append(f"Generated operational recommendation: {recommended_action_type}")

        # 5. Request Human Approval
        appr_res = json.loads(request_human_approval(incident_id, "Automated triage completed. Response plan awaits supervisor sign-off."))
        tool_traces.append({"tool": "request_human_approval", "result": appr_res, "timestamp": datetime.now(timezone.utc).isoformat()})
        actions_taken.append("Submitted action plan to supervisor approval queue")

        # 6. Retrieve authoritative fresh incident from repository
        inc = self.service.repo.get(incident_id)
        
        # Invoke inference adapter for summary explanation
        inference_out = self.adapter.invoke_endpoint({
            "message": f"Explain waterlogging risk and response recommendation for {incident_id}",
            "incident_context": inc.model_dump() if inc else {},
            "tool_outputs": tool_traces
        })

        rec = inc.recommended_action if inc else {}
        recs_list = [f"{rec.get('action_type')}: {rec.get('equipment')} ({rec.get('assigned_unit')})"] if rec else []

        return {
            "response": inference_out.get("response", ""),
            "incident_id": incident_id,
            "incident_status": inc.status.value if inc else "UNKNOWN",
            "risk_score": inc.risk_assessment.risk_score if inc and inc.risk_assessment else None,
            "severity": inc.risk_assessment.severity.value if inc and inc.risk_assessment else None,
            "reasoning_summary": inference_out.get("reasoning_summary") or (inc.risk_assessment.explanation if inc and inc.risk_assessment else ""),
            "recommendations": recs_list,
            "actions_taken": actions_taken,
            "next_steps": [
                "Review incident in Supervisor Dispatch Queue",
                "Authorize equipment deployment to create field response task",
                "Monitor real-time culvert sensor telemetry"
            ],
            # Diagnostic telemetry for server logs / admin inspect
            "debug": {
                "tool_traces": tool_traces,
                "is_mock": inference_out.get("is_mock", True),
                "adapter": inference_out.get("adapter", "MockSageMakerInferenceAdapter")
            }
        }

    def chat_with_agent(self, message: str, incident_id: Optional[str] = None) -> Dict[str, Any]:
        """Provides an authoritative conversational interface for dispatchers and supervisors."""
        context = {}
        tool_traces: List[Dict[str, Any]] = []
        actions_taken: List[str] = []

        # Always pull authoritative incident state from the configured repository
        inc = None
        if incident_id:
            inc = self.service.repo.get(incident_id)
            if inc:
                msg_lower = message.lower()
                # Run appropriate tool if requested and state permits
                if ("risk" in msg_lower or "score" in msg_lower) and not inc.risk_assessment:
                    res = json.loads(calculate_waterlogging_risk(incident_id))
                    tool_traces.append({"tool": "calculate_waterlogging_risk", "result": res})
                    actions_taken.append(f"Executed risk engine: {res.get('risk_score')}/100")
                    inc = self.service.repo.get(incident_id)
                elif ("prioritize" in msg_lower or "rank" in msg_lower) and not inc.priority:
                    res = json.loads(prioritize_incident(incident_id))
                    tool_traces.append({"tool": "prioritize_incident", "result": res})
                    actions_taken.append(f"Ranked incident: #{res.get('priority_rank')}")
                    inc = self.service.repo.get(incident_id)
                elif ("recommend" in msg_lower or "action" in msg_lower) and not inc.recommended_action:
                    res = json.loads(recommend_response(incident_id))
                    tool_traces.append({"tool": "recommend_response", "result": res})
                    actions_taken.append("Formulated response recommendation")
                    inc = self.service.repo.get(incident_id)

                context = inc.model_dump()

        inference_out = self.adapter.invoke_endpoint({
            "message": message,
            "incident_context": context,
            "tool_outputs": tool_traces
        })

        # Build authoritative response metadata
        rec = inc.recommended_action if inc else {}
        recs_list = []
        if rec:
            recs_list.append(f"{rec.get('action_type')}: {rec.get('equipment')} ({rec.get('assigned_unit')})")

        next_steps = []
        if inc:
            if inc.status.value == "NEW":
                next_steps.append("Run automated risk calculation")
            elif inc.status.value == "AWAITING_APPROVAL":
                next_steps.append("Human supervisor review required before equipment dispatch")
            elif inc.status.value == "IN_PROGRESS":
                next_steps.append("Awaiting field crew dewatering completion notes and evidence photo")
            elif inc.status.value == "RESOLVED":
                next_steps.append("Verify post-clearance sensor telemetry flow rate and water depth")
            elif inc.status.value == "VERIFIED":
                next_steps.append("Incident verified and archived")
            elif inc.status.value == "NEEDS_HUMAN_REVIEW":
                next_steps.append("Secondary field inspection required due to persistent water level or sensor anomaly")

        return {
            "response": inference_out.get("response", ""),
            "incident_id": incident_id,
            "incident_status": inc.status.value if inc else None,
            "risk_score": inc.risk_assessment.risk_score if inc and inc.risk_assessment else None,
            "severity": inc.risk_assessment.severity.value if inc and inc.risk_assessment else None,
            "reasoning_summary": inference_out.get("reasoning_summary", ""),
            "recommendations": recs_list,
            "actions_taken": actions_taken,
            "next_steps": next_steps,
            # Protected debug info for server logs / admin inspect
            "debug": {
                "tool_traces": tool_traces,
                "is_mock": inference_out.get("is_mock", True),
                "adapter": inference_out.get("adapter", "MockSageMakerInferenceAdapter")
            }
        }

_orchestrator: Optional[MonsoonAgentOrchestrator] = None

def get_orchestrator() -> MonsoonAgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MonsoonAgentOrchestrator()
    return _orchestrator
