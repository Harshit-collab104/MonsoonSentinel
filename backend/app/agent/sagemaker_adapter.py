import os
import json
import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class SageMakerInferenceAdapter:
    """Adapter for Amazon SageMaker AI model inference.
    
    In local development (mock mode), this provides deterministic, explainable
    model reasoning and tool invocation guidance without requiring AWS credentials
    or incurring cloud billing.
    
    When configured with a deployed SageMaker endpoint, it uses standard IAM role
    or local AWS profile credentials via boto3 (no credentials are ever hardcoded).
    """

    def __init__(
        self,
        endpoint_name: Optional[str] = None,
        region_name: Optional[str] = None,
        mock_mode: Optional[bool] = None
    ):
        self.endpoint_name = endpoint_name or settings.SAGEMAKER_ENDPOINT_NAME
        self.region_name = region_name or settings.AWS_REGION
        self.mock_mode = settings.USE_MOCK_SAGEMAKER if mock_mode is None else mock_mode
        self._client = None

    def _get_sagemaker_client(self):
        if self._client is None and not self.mock_mode:
            try:
                import boto3
                self._client = boto3.client("sagemaker-runtime", region_name=self.region_name)
            except Exception as e:
                logger.warning(f"Failed to initialize AWS boto3 client: {e}. Falling back to mock adapter.")
                self.mock_mode = True
        return self._client

    def invoke_endpoint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invokes the SageMaker model endpoint or local mock adapter."""
        if self.mock_mode:
            return self._mock_inference(payload)

        # Real SageMaker Endpoint Invocation
        client = self._get_sagemaker_client()
        if not client:
            return self._mock_inference(payload)

        try:
            response = client.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Accept="application/json",
                Body=json.dumps(payload).encode("utf-8")
            )
            result = json.loads(response["Body"].read().decode("utf-8"))
            return {
                "is_mock": False,
                "endpoint": self.endpoint_name,
                "result": result
            }
        except Exception as e:
            logger.error(f"SageMaker endpoint invocation error: {e}")
            # Resilient fallback to mock inference in local dev
            mock_res = self._mock_inference(payload)
            mock_res["error_fallback"] = str(e)
            return mock_res

    def _mock_inference(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic, domain-aware mock inference simulating an instruction-tuned LLM
        specialized for municipal flood triage.
        """
        user_message = payload.get("message", "")
        incident_context = payload.get("incident_context", {})
        tool_outputs = payload.get("tool_outputs", {})

        # Extract incident info if provided
        inc_id = incident_context.get("id", "N/A")
        status = incident_context.get("status", "NEW")
        risk = incident_context.get("risk_assessment") or {}
        score = risk.get("risk_score", 0.0)
        sev = risk.get("severity", "UNKNOWN")

        # Synthesize explainable agent response
        thought_process = [
            f"1. Inspected incident context for {inc_id} (Status: {status}).",
            "2. Consulted deterministic Python risk engine output.",
            f"3. Recorded risk score: {score}/100 with severity {sev}.",
            "4. Verified sensor telemetry & municipal drain capacity constraints.",
            "5. Formulated actionable municipal dispatch recommendation."
        ]

        if "risk" in user_message.lower() or "score" in user_message.lower():
            text = (
                f"**Waterlogging Risk Assessment for {inc_id}**\n\n"
                f"- **Overall Risk Score:** `{score}/100` ({sev})\n"
                f"- **Formula Used:** Multi-factor weighted sum with uncertainty penalties for missing data.\n"
                f"- **Explanation:** {risk.get('explanation', 'Risk calculated deterministically from rainfall and blockage data.')}\n"
                f"\n*Note: Score was calculated deterministically by the Python Risk Engine.*"
            )
        elif "recommend" in user_message.lower() or "action" in user_message.lower() or "approve" in user_message.lower():
            rec = incident_context.get("recommended_action") or {}
            text = (
                f"**Response Recommendation for {inc_id}**\n\n"
                f"- **Action Type:** `{rec.get('action_type', 'DEPLOY_DEWATERING_PUMP')}`\n"
                f"- **Assigned Crew:** {rec.get('assigned_unit', 'Municipal Rapid Response Division')}\n"
                f"- **Required Equipment:** {rec.get('equipment', 'High-pressure vacuum pump')}\n"
                f"- **Supervisor Approval Required:** Yes (`AWAITING_APPROVAL`)\n\n"
                f"> **Important:** Physical drain clearance has *not* occurred yet. Approval must be granted by a human supervisor before dispatch."
            )
        else:
            text = (
                f"Hello, I am **Monsoon Sentinel Assistant** (running on local Strands Agents SDK with SageMaker Mock Adapter).\n\n"
                f"Currently tracking incident `{inc_id}` in status `{status}` with severity `{sev}`.\n"
                f"I can calculate risk, prioritize urgency, recommend response equipment, submit for supervisor approval, and verify drainage telemetry."
            )

        return {
            "is_mock": True,
            "adapter": "MockSageMakerInferenceAdapter (Local Development)",
            "endpoint_name": self.endpoint_name,
            "thought_process": thought_process,
            "response": text,
            "suggested_next_tool": "recommend_response" if status == "PRIORITIZED" else "request_human_approval"
        }
