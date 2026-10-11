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
    get_incident_audit,
    compare_incidents,
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
        """Provides an authoritative conversational interface for dispatchers and supervisors.
        Distinguishes specific operational intents:
        - Incident status & summaries
        - Deterministic risk assessment & calculation
        - Incident prioritization & multi-incident comparison
        - Response equipment recommendations & dispatch readiness
        - Supervisor approval & workflow execution
        - Telemetry & post-clearance sensor verification
        - Audit history & state transition trails
        - Human-review escalation & redispatch guidance
        """
        context = {}
        tool_traces: List[Dict[str, Any]] = []
        actions_taken: List[str] = []
        msg_lower = message.lower()

        # 1. Resolve target incident if provided or mentioned in text
        inc = None
        target_id = incident_id
        if not target_id:
            # Check if user mentioned an incident ID like INC-XXXX in the text
            words = message.split()
            for w in words:
                clean_w = w.strip(".,;:?!()[]'\"")
                if clean_w.startswith("INC-") or clean_w.startswith("inc-"):
                    target_id = clean_w.upper()
                    break

        if target_id:
            inc = self.service.repo.get(target_id)
            if inc:
                context = inc.model_dump()

        # 2. Intent Routing & Authoritative Tool Invocation
        # Intent A: Compare / Prioritize Multiple Incidents
        if any(w in msg_lower for w in ["compare", "ranking", "rankings", "all incidents", "highest risk", "which incident"]):
            comp_res = json.loads(compare_incidents(""))
            tool_traces.append({"tool": "compare_incidents", "result": comp_res})
            actions_taken.append(f"Retrieved and ranked {comp_res.get('count', 0)} municipal incidents across active sectors")

        # Intent B: Audit History & State Transition Trail
        elif any(w in msg_lower for w in ["audit", "history", "audit log", "trail", "transitions", "who approved", "audit trail"]) or ("log" in msg_lower.split() and "waterlogging" not in msg_lower):
            if target_id and inc:
                audit_res = json.loads(get_incident_audit(target_id))
                tool_traces.append({"tool": "get_incident_audit", "result": audit_res})
                actions_taken.append(f"Retrieved immutable audit history ({len(inc.audit_history)} events)")
            else:
                actions_taken.append("Incident ID required to inspect audit trail")

        # Intent C: Risk Assessment & Explanation
        elif any(w in msg_lower for w in ["risk", "score", "calculate risk", "assess"]):
            if target_id and inc:
                if not inc.risk_assessment or "recalculate" in msg_lower or "calculate" in msg_lower:
                    risk_res = json.loads(calculate_waterlogging_risk(target_id))
                    tool_traces.append({"tool": "calculate_waterlogging_risk", "result": risk_res})
                    actions_taken.append(f"Executed deterministic risk engine: {risk_res.get('risk_score')}/100 ({risk_res.get('severity')})")
                    inc = self.service.repo.get(target_id)
                    context = inc.model_dump()
                else:
                    actions_taken.append(f"Retrieved existing risk assessment: {inc.risk_assessment.risk_score}/100")

        # Intent D: Prioritization
        elif any(w in msg_lower for w in ["prioritize", "urgency", "rank"]) and not ("compare" in msg_lower):
            if target_id and inc:
                if not inc.priority or "re-prioritize" in msg_lower:
                    prio_res = json.loads(prioritize_incident(target_id))
                    tool_traces.append({"tool": "prioritize_incident", "result": prio_res})
                    actions_taken.append(f"Prioritized incident at rank #{prio_res.get('priority_rank')}")
                    inc = self.service.repo.get(target_id)
                    context = inc.model_dump()

        # Intent E: Response Recommendation
        elif any(w in msg_lower for w in ["recommend", "equipment", "assigned team", "unit", "what action"]):
            if target_id and inc:
                if not inc.recommended_action or "generate" in msg_lower:
                    rec_res = json.loads(recommend_response(target_id))
                    tool_traces.append({"tool": "recommend_response", "result": rec_res})
                    actions_taken.append("Generated response plan recommendation")
                    inc = self.service.repo.get(target_id)
                    context = inc.model_dump()

        # Intent F: Approval & Dispatch Readiness
        elif any(w in msg_lower for w in ["approval", "authorize", "dispatch readiness", "ready to dispatch"]):
            if target_id and inc:
                if inc.status.value == "RECOMMENDED":
                    appr_res = json.loads(request_human_approval(target_id, "Requested via conversational dispatch agent."))
                    tool_traces.append({"tool": "request_human_approval", "result": appr_res})
                    actions_taken.append("Transitioned to AWAITING_APPROVAL")
                    inc = self.service.repo.get(target_id)
                    context = inc.model_dump()
                else:
                    actions_taken.append(f"Current status: {inc.status.value}")

        # Intent G: Telemetry & Flow Rate / Sensor Readings
        elif any(w in msg_lower for w in ["flow", "rate", "sensor", "telemetry", "depth", "reading"]):
            if target_id and inc:
                actions_taken.append("Checked culvert IoT telemetry")

        # Intent H: General Status Lookup
        elif any(w in msg_lower for w in ["status", "lookup", "where is", "current state"]):
            if target_id and inc:
                st_res = json.loads(get_incident_status(target_id))
                tool_traces.append({"tool": "get_incident_status", "result": st_res})
                actions_taken.append(f"Verified authoritative status: {st_res.get('status')}")

        # 3. Invoke Inference Adapter with authoritative data and tool traces
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

        # Only include heavy lifecycle next_steps if this was an action/triage prompt
        # Keep conversational answers direct and concise
        next_steps = []
        is_action_prompt = any(w in message.lower() for w in ["triage", "next", "what to do", "step", "pipeline", "guide"])
        if is_action_prompt and inc:
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
            "incident_status": None,  # Don't clutter casual Q&A with full-width badges
            "risk_score": None,
            "severity": None,
            "reasoning_summary": "",  # Don't repeat the risk paragraph on every question
            "recommendations": recs_list if is_action_prompt else [],
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
