import os
import re
import json
import logging
from typing import Dict, Any, Optional, List

from botocore.exceptions import (
    ClientError,
    BotoCoreError,
    ReadTimeoutError,
    ConnectTimeoutError,
    EndpointConnectionError,
)

from app.core.config import settings
from app.core.exceptions import SageMakerConfigurationError, SageMakerInvocationError

logger = logging.getLogger(__name__)


class SageMakerInferenceAdapter:
    """Adapter for Amazon SageMaker AI model inference.

    Supports two distinct execution modes:

    1. Mock Mode (USE_MOCK_SAGEMAKER=true):
       - Uses deterministic, domain-aware flood triage reasoning.
       - Runs entirely offline without requiring AWS credentials or cloud billing.
       - Used for local development, CI/CD, and offline demonstration.

    2. Real Inference Mode (USE_MOCK_SAGEMAKER=false):
       - Uses boto3 sagemaker-runtime client to invoke real deployed SageMaker endpoints.
       - Validates endpoint configuration and payload schemas.
       - Multi-schema support: Hugging Face TGI, AWS JumpStart LLMs (Llama 3, Mistral),
         OpenAI-compatible chat completions, and custom container JSON schemas.
       - Comprehensive error handling: AccessDenied, ModelError, timeouts, malformed output.
       - Strictly enforces fail-loud behavior: NEVER silently falls back to mock results.
       - Sanitizes output to prevent leaking private chain-of-thought or raw thought blocks.
    """

    def __init__(
        self,
        endpoint_name: Optional[str] = None,
        region_name: Optional[str] = None,
        mock_mode: Optional[bool] = None,
    ):
        self.endpoint_name = (
            endpoint_name if endpoint_name is not None else settings.SAGEMAKER_ENDPOINT_NAME
        )
        self.region_name = region_name or settings.AWS_REGION
        self.mock_mode = (
            settings.USE_MOCK_SAGEMAKER if mock_mode is None else mock_mode
        )
        self._client = None

    def _get_sagemaker_client(self):
        """Initializes or returns cached boto3 sagemaker-runtime client."""
        if self._client is None and not self.mock_mode:
            try:
                import boto3

                self._client = boto3.client(
                    "sagemaker-runtime", region_name=self.region_name
                )
            except Exception as e:
                logger.error(
                    f"Failed to initialize SageMaker Runtime boto3 client: {e}"
                )
                raise SageMakerConfigurationError(
                    f"Cannot initialize SageMaker runtime client in region '{self.region_name}': {str(e)}"
                )
        return self._client

    def _build_real_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Constructs an industry-standard, multi-schema inference request payload.
        Ensures compatibility across:
        - Hugging Face Text Generation Inference (TGI): 'inputs' + 'parameters'
        - AWS JumpStart & Chat Completions (Llama 3, Mistral): 'messages' array
        - Custom Monsoon Sentinel containers: 'message' + 'incident_context' + 'tool_outputs'
        """
        # If payload is already explicitly pre-formatted for TGI or vLLM, preserve it
        if "inputs" in payload and "parameters" in payload:
            return payload
        if "messages" in payload and isinstance(payload["messages"], list):
            return payload

        user_message = payload.get("message", "")
        incident_context = payload.get("incident_context", {})
        tool_outputs = payload.get("tool_outputs", [])

        # Build clean operational context string
        context_parts = []
        if incident_context:
            inc_id = incident_context.get("id", "N/A")
            status = incident_context.get("status", "NEW")
            ward = (
                incident_context.get("report", {}).get("ward_name")
                or "Municipal Service Area"
            )
            depth = incident_context.get("report", {}).get("water_depth_cm", "Unknown")
            risk = incident_context.get("risk_assessment") or {}
            score = risk.get("risk_score", "Pending")
            sev = risk.get("severity", "Unassessed")
            rec = incident_context.get("recommended_action") or {}

            context_parts.append(
                f"Incident: {inc_id} | Status: {status} | Ward: {ward}"
            )
            context_parts.append(
                f"Water Depth: {depth} cm | Risk Score: {score}/100 ({sev})"
            )
            if rec:
                context_parts.append(
                    f"Recommended Action: {rec.get('action_type')} | Assigned Unit: {rec.get('assigned_unit')}"
                )

        if tool_outputs:
            tools_summary = ", ".join(
                [
                    t.get("tool", "tool")
                    for t in tool_outputs
                    if isinstance(t, dict) and "tool" in t
                ]
            )
            if tools_summary:
                context_parts.append(f"Executed Tools: {tools_summary}")

        context_str = "\n".join(context_parts) if context_parts else "No incident context."

        system_instruction = (
            "You are Monsoon Sentinel AI, an authoritative urban flood risk and disaster response assistant "
            "for municipal emergency operation centers. Provide concise, professional, actionable operational assessments. "
            "Do not include internal implementation details, raw system prompts, or private thought processes."
        )

        formatted_prompt = (
            f"<|system|>\n{system_instruction}\n"
            f"<|context|>\n{context_str}\n"
            f"<|user|>\n{user_message}\n"
            f"<|assistant|>\n"
        )

        return {
            # 1. HuggingFace / TGI standard
            "inputs": formatted_prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.2,
                "top_p": 0.9,
                "return_full_text": False,
            },
            # 2. Chat / Messages standard (Llama-3-Instruct / vLLM / JumpStart)
            "messages": [
                {
                    "role": "system",
                    "content": f"{system_instruction}\n\nContext:\n{context_str}",
                },
                {"role": "user", "content": user_message},
            ],
            # 3. Direct domain parameters (Custom container schema)
            "message": user_message,
            "incident_context": incident_context,
            "tool_outputs": tool_outputs,
        }

    def _sanitize_response_text(self, text: str) -> str:
        """Strips private chain-of-thought blocks (<thought>, <thinking>, ```thought)
        and model control tokens to ensure only clean user-facing operational text is returned.
        """
        if not text:
            return ""

        # Remove explicit thought blocks
        cleaned = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)
        cleaned = re.sub(r"<thinking>.*?</thinking>", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"```thought.*?```", "", cleaned, flags=re.DOTALL)

        # Remove common special tokens
        cleaned = re.sub(r"<\|im_end\|>|<\|end_of_text\|>|</s>|<\|eot_id\|>", "", cleaned)

        # Strip excessive leading/trailing blank lines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _parse_model_response(self, raw_body: str) -> Dict[str, Any]:
        """Parses and validates the raw JSON response returned by the SageMaker model.
        Extracts generated text and reasoning summary across TGI, Chat, and custom formats.
        Raises SageMakerInvocationError if response is empty, unparseable, or invalid.
        """
        if not raw_body or not raw_body.strip():
            raise SageMakerInvocationError(
                self.endpoint_name,
                "SageMaker endpoint returned an empty response body.",
            )

        try:
            result = json.loads(raw_body)
        except json.JSONDecodeError as e:
            raise SageMakerInvocationError(
                self.endpoint_name,
                f"SageMaker endpoint returned non-JSON response body: {str(e)}",
            )

        generated_text = ""
        reasoning_summary = ""

        # Format 1: List of dicts (Hugging Face TGI standard: [{"generated_text": "..."}])
        if isinstance(result, list):
            if len(result) > 0 and isinstance(result[0], dict):
                generated_text = (
                    result[0].get("generated_text")
                    or result[0].get("text")
                    or result[0].get("response")
                    or ""
                )
            elif len(result) > 0 and isinstance(result[0], str):
                generated_text = result[0]
            else:
                generated_text = str(result)

        # Format 2: Dict response
        elif isinstance(result, dict):
            # Check for explicit model error
            if "error" in result:
                raise SageMakerInvocationError(
                    self.endpoint_name,
                    f"Model reported execution error: {result['error']}",
                )

            # Direct custom response
            if "response" in result and isinstance(result["response"], str):
                generated_text = result["response"]
            # HF TGI object
            elif "generated_text" in result and isinstance(result["generated_text"], str):
                generated_text = result["generated_text"]
            # OpenAI / vLLM chat choices
            elif (
                "choices" in result
                and isinstance(result["choices"], list)
                and len(result["choices"]) > 0
            ):
                first_choice = result["choices"][0]
                if isinstance(first_choice, dict):
                    msg = first_choice.get("message")
                    if isinstance(msg, dict):
                        generated_text = msg.get("content", "")
                    else:
                        generated_text = first_choice.get("text", "")
            # Direct text field
            elif "text" in result and isinstance(result["text"], str):
                generated_text = result["text"]
            # Fallback output
            elif "output" in result:
                generated_text = str(result["output"])
            else:
                generated_text = str(result)

            reasoning_summary = (
                result.get("reasoning_summary") or result.get("summary") or ""
            )

        elif isinstance(result, str):
            generated_text = result

        # Validate that non-empty text was generated
        if not generated_text or not generated_text.strip():
            raise SageMakerInvocationError(
                self.endpoint_name,
                "Model response contains no generated text or content.",
            )

        cleaned_text = self._sanitize_response_text(generated_text)

        return {
            "response": cleaned_text,
            "reasoning_summary": reasoning_summary,
            "raw_result": result,
        }

    def invoke_endpoint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invokes the SageMaker model endpoint or local mock adapter.
        
        Guarantees:
        - When USE_MOCK_SAGEMAKER=true: uses local mock adapter.
        - When USE_MOCK_SAGEMAKER=false: invokes real SageMaker endpoint via boto3.
        - NEVER silently falls back to mock results on failure in real mode.
        """
        if self.mock_mode:
            logger.info(
                "Executing mock SageMaker inference adapter (USE_MOCK_SAGEMAKER=true)."
            )
            return self._mock_inference(payload)

        # Real SageMaker Endpoint Invocation Validation
        if not self.endpoint_name or not self.endpoint_name.strip() or self.endpoint_name.startswith("mock-"):
            raise SageMakerConfigurationError(
                f"Real SageMaker inference is enabled (USE_MOCK_SAGEMAKER=false), but SAGEMAKER_ENDPOINT_NAME "
                f"('{self.endpoint_name}') is unconfigured, empty, or a placeholder. A real SageMaker endpoint must be deployed."
            )

        client = self._get_sagemaker_client()
        real_payload = self._build_real_payload(payload)

        try:
            logger.info(
                f"Invoking real SageMaker endpoint '{self.endpoint_name}' in region '{self.region_name}'..."
            )
            response = client.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Accept="application/json",
                Body=json.dumps(real_payload).encode("utf-8"),
            )

            raw_body = response["Body"].read().decode("utf-8")
            parsed = self._parse_model_response(raw_body)

            return {
                "is_mock": False,
                "endpoint": self.endpoint_name,
                "response": parsed["response"],
                "reasoning_summary": parsed["reasoning_summary"],
                "raw_result": parsed["raw_result"],
            }

        except SageMakerConfigurationError:
            raise

        except SageMakerInvocationError:
            raise

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error(
                f"SageMaker ClientError [{error_code}] on '{self.endpoint_name}': {error_msg}"
            )

            if error_code in ["AccessDeniedException", "UnauthorizedException"]:
                msg = (
                    f"Access denied invoking SageMaker endpoint '{self.endpoint_name}'. "
                    f"Ensure IAM execution role has 'sagemaker:InvokeEndpoint' permission: {error_msg}"
                )
            elif error_code == "ValidationException":
                msg = (
                    f"Validation failed for SageMaker endpoint '{self.endpoint_name}'. "
                    f"Check endpoint name, payload schema, or ContentType: {error_msg}"
                )
            elif error_code == "ModelError":
                msg = f"Model execution error on SageMaker endpoint '{self.endpoint_name}': {error_msg}"
            elif error_code == "ModelNotReadyException":
                msg = f"SageMaker endpoint '{self.endpoint_name}' is not ready: {error_msg}"
            else:
                msg = f"AWS ClientError [{error_code}]: {error_msg}"

            raise SageMakerInvocationError(self.endpoint_name, msg)

        except (ReadTimeoutError, ConnectTimeoutError) as e:
            logger.error(f"SageMaker timeout on '{self.endpoint_name}': {e}")
            raise SageMakerInvocationError(
                self.endpoint_name,
                f"Inference request timed out on endpoint '{self.endpoint_name}': {str(e)}",
            )

        except EndpointConnectionError as e:
            logger.error(f"SageMaker connection error on '{self.endpoint_name}': {e}")
            raise SageMakerInvocationError(
                self.endpoint_name,
                f"Could not connect to SageMaker endpoint '{self.endpoint_name}' in region '{self.region_name}': {str(e)}",
            )

        except (BotoCoreError, Exception) as e:
            logger.error(
                f"SageMaker invocation error on '{self.endpoint_name}': {e}"
            )
            raise SageMakerInvocationError(self.endpoint_name, str(e))

    def _mock_inference(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic domain-aware mock inference specialized for municipal flood triage.
        Produces professional, concise operational responses without implementation jargon.
        """
        user_message = payload.get("message", "")
        incident_context = payload.get("incident_context", {})

        inc_id = incident_context.get("id", "N/A")
        status = incident_context.get("status", "NEW")
        ward = (
            incident_context.get("report", {}).get("ward_name")
            or "Municipal Service Area"
        )
        risk = incident_context.get("risk_assessment") or {}
        score = risk.get("risk_score")
        sev = risk.get("severity") or "UNASSESSED"
        rec = incident_context.get("recommended_action") or {}
        task = incident_context.get("response_task") or {}
        ver = incident_context.get("verification") or {}

        msg_lower = user_message.lower()

        # Build concise reasoning summary from authoritative data
        reasoning_summary = ""
        if score is not None:
            reasoning_summary = (
                f"Risk evaluated at {score}/100 ({sev}) based on rainfall telemetry, "
                f"drain blockage level, and historical ward hotspot data."
            )
        elif "risk" in msg_lower:
            reasoning_summary = "Risk assessment pending calculation from live telemetry."

        if "flow" in msg_lower or "rate" in msg_lower or "sensor" in msg_lower or "telemetry" in msg_lower:
            if ver:
                flow = ver.get("sensor_flow_rate_lps", "N/A")
                res_depth = ver.get("post_clearance_depth_cm", "N/A")
                is_ver = ver.get("verified", False)
                notes = ver.get("notes", "No sensor notes.")
                text = (
                    f"**Sensor Telemetry & Verification for {inc_id}**\n\n"
                    f"- **Culvert Discharge Flow Rate:** `{flow} L/s`\n"
                    f"- **Residual Post-Clearance Depth:** `{res_depth} cm`\n"
                    f"- **Verification Outcome:** {'✅ Verified (Passed)' if is_ver else '⚠️ Flagged (Needs Review)'}\n"
                    f"- **Telemetry Notes:** {notes}\n"
                    f"- **Sensor Type:** {'Simulated IoT Sensor' if ver.get('simulated') else 'Live Hardware Probe'}"
                )
            else:
                text = f"Incident `{inc_id}` has not undergone post-clearance sensor verification yet. Current lifecycle state is `{status}`."

        elif "verify" in msg_lower or "verification" in msg_lower or "clearance" in msg_lower:
            if ver:
                is_ver = ver.get("verified", False)
                text = (
                    f"**Verification Report for {inc_id}**\n\n"
                    f"- **Status:** {'VERIFIED' if is_ver else 'NEEDS_HUMAN_REVIEW'}\n"
                    f"- **Discharge Flow:** `{ver.get('sensor_flow_rate_lps', 0)} L/s`\n"
                    f"- **Residual Water Level:** `{ver.get('post_clearance_depth_cm', 0)} cm`\n"
                    f"- **Audited Notes:** {ver.get('notes', 'Automated sensor check.')}\n\n"
                    f"{'The stormwater drain is operating at normal capacity.' if is_ver else 'Anomaly detected: discharge flow remains restricted.'}"
                )
            else:
                text = f"Incident `{inc_id}` has not completed post-clearance verification yet."

        elif "summary" in msg_lower or "debrief" in msg_lower or "report" in msg_lower:
            text = (
                f"**Executive Incident Debrief: {inc_id}**\n\n"
                f"- **Sector:** {ward}\n"
                f"- **Current State:** `{status}`\n"
                f"- **Initial Water Depth:** {incident_context.get('report', {}).get('water_depth_cm', 0)} cm\n"
                f"- **Evaluated Risk:** `{score}/100` ({sev})\n"
                f"- **Dispatched Unit:** {task.get('assigned_unit', rec.get('assigned_unit', 'Rapid Response Division'))}\n"
                f"- **Verification Status:** {'Passed' if ver.get('verified') else ('Pending' if not ver else 'Under Review')}\n"
                f"- **Sensor Discharge:** {ver.get('sensor_flow_rate_lps', 'N/A')} L/s\n\n"
                f"This incident has completed municipal emergency triage and response lifecycle."
            )

        elif "risk" in msg_lower or "score" in msg_lower:
            if score is not None:
                text = (
                    f"**Waterlogging Risk Assessment for {inc_id}**\n\n"
                    f"- **Location:** {ward}\n"
                    f"- **Calculated Risk:** `{score}/100` ({sev})\n"
                    f"- **Current Lifecycle State:** `{status}`\n"
                    f"- **Assessment Basis:** {risk.get('explanation', 'Multi-factor evaluation incorporating rainfall intensity, drain obstruction, and localized historical pooling.')}"
                )
            else:
                text = f"Incident `{inc_id}` currently has no computed risk score. Telemetry analysis is required."

        elif "recommend" in msg_lower or "action" in msg_lower or "team" in msg_lower or "crew" in msg_lower:
            if rec or task:
                action_type = task.get("action_type") or rec.get("action_type", "DEPLOY_DEWATERING_PUMP")
                assigned = task.get("assigned_unit") or rec.get("assigned_unit", "Municipal Rapid Response")
                equip = task.get("equipment") or rec.get("equipment", "High-capacity dewatering pump")
                text = (
                    f"**Response Plan for {inc_id}**\n\n"
                    f"- **Action Type:** `{action_type}`\n"
                    f"- **Assigned Team:** {assigned}\n"
                    f"- **Equipment:** {equip}\n"
                    f"- **Task Status:** {'Active Task ' + task.get('task_id', '') if task else 'Awaiting Approval'}\n"
                )
            else:
                text = f"No recommended response has been generated for incident `{inc_id}` yet. Triage analysis is required."

        elif "status" in msg_lower:
            text = (
                f"**Operational Status for {inc_id}**\n\n"
                f"- **Status:** `{status}`\n"
                f"- **Location:** {ward}\n"
                f"- **Risk Tier:** `{sev}` ({score if score is not None else 'N/A'}/100)\n"
                f"- **Active Task:** {task.get('action_type', 'None') if task else 'None'}\n"
                f"- **Verification:** {'Verified (Flow: ' + str(ver.get('sensor_flow_rate_lps', '')) + ' L/s)' if ver.get('verified') else 'Pending'}"
            )

        else:
            if inc_id != "N/A":
                text = (
                    f"**Monsoon Sentinel Field Operations: {inc_id}**\n\n"
                    f"- **Location:** {ward}\n"
                    f"- **Current Status:** `{status}`\n"
                    f"- **Assessed Risk:** `{score}/100` ({sev})\n"
                    f"{'- **Final Culvert Discharge:** `' + str(ver.get('sensor_flow_rate_lps', 'N/A')) + ' L/s` (Verified)' if ver.get('verified') else ''}\n\n"
                    f"You can ask about risk breakdown, crew recommendations, or post-clearance sensor telemetry."
                )
            else:
                text = (
                    f"**Monsoon Sentinel Central Dispatch**\n\n"
                    f"Urban flood risk monitoring and response system active. Select an incident from the roster "
                    f"to review telemetry, calculate drainage risk, or coordinate municipal field crews."
                )

        return {
            "is_mock": True,
            "adapter": "MockSageMakerInferenceAdapter",
            "endpoint_name": self.endpoint_name,
            "response": text,
            "reasoning_summary": reasoning_summary,
        }
