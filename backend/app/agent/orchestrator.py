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
        """Runs the AI triage pipeline through Strands tools:
        1. Telemetry & historical analysis
        2. Deterministic risk calculation
        3. Multi-incident prioritization
        4. Response recommendation
        5. Submit for human approval
        """
        tool_traces: List[Dict[str, Any]] = []

        # 1. Inspect status
        st_res = json.loads(get_incident_status(incident_id))
        tool_traces.append({"tool": "get_incident_status", "result": st_res, "timestamp": datetime.now(timezone.utc).isoformat()})

        # 2. Risk Calculation
        risk_res = json.loads(calculate_waterlogging_risk(incident_id))
        tool_traces.append({"tool": "calculate_waterlogging_risk", "result": risk_res, "timestamp": datetime.now(timezone.utc).isoformat()})

        # 3. Prioritization
        prio_res = json.loads(prioritize_incident(incident_id))
        tool_traces.append({"tool": "prioritize_incident", "result": prio_res, "timestamp": datetime.now(timezone.utc).isoformat()})

        # 4. Recommendation
        rec_res = json.loads(recommend_response(incident_id))
        tool_traces.append({"tool": "recommend_response", "result": rec_res, "timestamp": datetime.now(timezone.utc).isoformat()})

        # 5. Request Human Approval
        appr_res = json.loads(request_human_approval(incident_id, "Triage complete. Awaiting supervisor authorization."))
        tool_traces.append({"tool": "request_human_approval", "result": appr_res, "timestamp": datetime.now(timezone.utc).isoformat()})

        # 6. Model Explanation via SageMaker Adapter
        inc = self.service.repo.get(incident_id)
        inference_out = self.adapter.invoke_endpoint({
            "message": f"Explain waterlogging risk and response recommendation for {incident_id}",
            "incident_context": inc.model_dump() if inc else {},
            "tool_outputs": tool_traces
        })

        return {
            "incident_id": incident_id,
            "status": inc.status.value if inc else "UNKNOWN",
            "risk_score": inc.risk_assessment.risk_score if inc and inc.risk_assessment else None,
            "severity": inc.risk_assessment.severity.value if inc and inc.risk_assessment else None,
            "tool_traces": tool_traces,
            "agent_explanation": inference_out.get("response", ""),
            "adapter_metadata": {
                "is_mock": inference_out.get("is_mock", True),
                "adapter": inference_out.get("adapter", "MockSageMakerInferenceAdapter")
            }
        }

    def chat_with_agent(self, message: str, incident_id: Optional[str] = None) -> Dict[str, Any]:
        """Provides an interactive conversational interface for dispatchers and supervisors."""
        context = {}
        tool_traces = []

        if incident_id:
            inc = self.service.repo.get(incident_id)
            if inc:
                context = inc.model_dump()
                # Run appropriate tool if requested
                msg_lower = message.lower()
                if "risk" in msg_lower and not inc.risk_assessment:
                    res = json.loads(calculate_waterlogging_risk(incident_id))
                    tool_traces.append({"tool": "calculate_waterlogging_risk", "result": res})
                    inc = self.service.repo.get(incident_id)
                    context = inc.model_dump() if inc else {}
                elif "prioritize" in msg_lower or "rank" in msg_lower:
                    res = json.loads(prioritize_incident(incident_id))
                    tool_traces.append({"tool": "prioritize_incident", "result": res})
                    inc = self.service.repo.get(incident_id)
                    context = inc.model_dump() if inc else {}
                elif "recommend" in msg_lower and not inc.recommended_action:
                    res = json.loads(recommend_response(incident_id))
                    tool_traces.append({"tool": "recommend_response", "result": res})
                    inc = self.service.repo.get(incident_id)
                    context = inc.model_dump() if inc else {}

        inference_out = self.adapter.invoke_endpoint({
            "message": message,
            "incident_context": context,
            "tool_outputs": tool_traces
        })

        return {
            "response": inference_out.get("response", ""),
            "thought_process": inference_out.get("thought_process", []),
            "tool_traces": tool_traces,
            "incident_id": incident_id,
            "is_mock": inference_out.get("is_mock", True)
        }

_orchestrator: Optional[MonsoonAgentOrchestrator] = None

def get_orchestrator() -> MonsoonAgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MonsoonAgentOrchestrator()
    return _orchestrator
