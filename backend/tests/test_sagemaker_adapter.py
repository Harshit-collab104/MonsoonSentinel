import json
import pytest
from unittest.mock import MagicMock
from botocore.exceptions import (
    ClientError,
    ReadTimeoutError,
    EndpointConnectionError,
)

from app.agent.sagemaker_adapter import SageMakerInferenceAdapter
from app.core.exceptions import SageMakerConfigurationError, SageMakerInvocationError


def test_sagemaker_mock_mode_behavior():
    """Mock mode must remain completely deterministic, offline, and clean of internal labels."""
    adapter = SageMakerInferenceAdapter(mock_mode=True)
    res = adapter.invoke_endpoint({
        "message": "Assess risk for INC-001",
        "incident_context": {
            "id": "INC-001",
            "status": "ANALYZING",
            "report": {"ward_name": "Ward 12"},
            "risk_assessment": {
                "risk_score": 75.0,
                "severity": "CRITICAL",
                "explanation": "High rainfall",
            },
        },
    })
    assert res["is_mock"] is True
    assert "response" in res
    assert "reasoning_summary" in res
    assert "75.0/100" in res["response"]
    assert "running on local Strands Agents SDK" not in res["response"]
    assert "Mock Adapter" not in res["response"]


def test_sagemaker_real_mode_constructs_correct_request():
    """Real adapter must construct the correct SageMaker invoke_endpoint request structure."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-production-flood-endpoint",
        region_name="ap-south-1",
        mock_mode=False,
    )

    mock_boto_client = MagicMock()
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"response": "Deployment authorized.", "reasoning_summary": "Pumps needed."}'
    mock_boto_client.invoke_endpoint.return_value = {"Body": mock_body}
    adapter._client = mock_boto_client

    payload = {
        "message": "Prioritize incident INC-099",
        "incident_context": {
            "id": "INC-099",
            "status": "NEW",
            "report": {"ward_name": "Koramangala", "water_depth_cm": 45.0},
            "risk_assessment": {"risk_score": 88.0, "severity": "CRITICAL"},
        },
        "tool_outputs": [{"tool": "calculate_waterlogging_risk", "risk_score": 88.0}],
    }

    res = adapter.invoke_endpoint(payload)

    assert res["is_mock"] is False
    assert res["endpoint"] == "real-production-flood-endpoint"
    assert res["response"] == "Deployment authorized."
    assert res["reasoning_summary"] == "Pumps needed."

    # Inspect call arguments to boto3 invoke_endpoint
    mock_boto_client.invoke_endpoint.assert_called_once()
    kwargs = mock_boto_client.invoke_endpoint.call_args.kwargs
    assert kwargs["EndpointName"] == "real-production-flood-endpoint"
    assert kwargs["ContentType"] == "application/json"
    assert kwargs["Accept"] == "application/json"

    sent_body = json.loads(kwargs["Body"].decode("utf-8"))
    assert "inputs" in sent_body
    assert "parameters" in sent_body
    assert sent_body["parameters"]["max_new_tokens"] == 512
    assert "messages" in sent_body
    assert len(sent_body["messages"]) == 2
    assert "Koramangala" in sent_body["inputs"]


def test_sagemaker_real_mode_huggingface_tgi_schema():
    """Real adapter must parse standard Hugging Face TGI response ([{'generated_text': '...'}])."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-tgi-mistral-endpoint", mock_mode=False
    )

    mock_boto_client = MagicMock()
    mock_body = MagicMock()
    tgi_output = [{"generated_text": "Field crew dispatch recommended for culvert clearance."}]
    mock_body.read.return_value = json.dumps(tgi_output).encode("utf-8")
    mock_boto_client.invoke_endpoint.return_value = {"Body": mock_body}
    adapter._client = mock_boto_client

    res = adapter.invoke_endpoint({"message": "Recommend action"})
    assert res["is_mock"] is False
    assert res["response"] == "Field crew dispatch recommended for culvert clearance."


def test_sagemaker_real_mode_openai_chat_schema():
    """Real adapter must parse OpenAI / vLLM chat completions schema (choices.message.content)."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-vllm-llama3-endpoint", mock_mode=False
    )

    mock_boto_client = MagicMock()
    mock_body = MagicMock()
    chat_output = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Waterlogging risk is critical; deploy mobile dewatering pump.",
                }
            }
        ]
    }
    mock_body.read.return_value = json.dumps(chat_output).encode("utf-8")
    mock_boto_client.invoke_endpoint.return_value = {"Body": mock_body}
    adapter._client = mock_boto_client

    res = adapter.invoke_endpoint({"message": "Evaluate status"})
    assert res["is_mock"] is False
    assert "Waterlogging risk is critical" in res["response"]


def test_sagemaker_real_mode_sanitizes_private_thought():
    """Private chain-of-thought blocks (<thought>...</thought>) must be stripped from user output."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-reasoning-endpoint", mock_mode=False
    )

    mock_boto_client = MagicMock()
    mock_body = MagicMock()
    model_output = {
        "response": "<thought>Analyzing internal flood vectors and neural weights.</thought>High risk detected in Dadar underpass. Advise traffic diversion."
    }
    mock_body.read.return_value = json.dumps(model_output).encode("utf-8")
    mock_boto_client.invoke_endpoint.return_value = {"Body": mock_body}
    adapter._client = mock_boto_client

    res = adapter.invoke_endpoint({"message": "Status update"})
    assert "<thought>" not in res["response"]
    assert "Analyzing internal flood vectors" not in res["response"]
    assert "High risk detected in Dadar underpass" in res["response"]


def test_sagemaker_real_mode_unconfigured_endpoint_raises():
    """Real mode with placeholder endpoint must immediately raise SageMakerConfigurationError."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="mock-monsoon-sagemaker-endpoint", mock_mode=False
    )
    with pytest.raises(SageMakerConfigurationError) as exc_info:
        adapter.invoke_endpoint({"message": "test"})
    assert "unconfigured, empty, or a placeholder" in str(exc_info.value)


def test_sagemaker_real_mode_empty_endpoint_raises():
    """Real mode with empty endpoint name must raise SageMakerConfigurationError."""
    adapter = SageMakerInferenceAdapter(endpoint_name="", mock_mode=False)
    with pytest.raises(SageMakerConfigurationError):
        adapter.invoke_endpoint({"message": "test"})


def test_sagemaker_real_mode_access_denied_handled():
    """AccessDeniedException must be caught and raised as SageMakerInvocationError with IAM explanation."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-production-flood-endpoint", mock_mode=False
    )

    mock_boto_client = MagicMock()
    mock_boto_client.invoke_endpoint.side_effect = ClientError(
        {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "User is not authorized to perform: sagemaker:InvokeEndpoint",
            }
        },
        "InvokeEndpoint",
    )
    adapter._client = mock_boto_client

    with pytest.raises(SageMakerInvocationError) as exc_info:
        adapter.invoke_endpoint({"message": "Analyze"})
    assert "Access denied" in str(exc_info.value)
    assert "sagemaker:InvokeEndpoint" in str(exc_info.value)


def test_sagemaker_real_mode_model_error_handled():
    """ModelError from SageMaker backend must raise SageMakerInvocationError."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-production-flood-endpoint", mock_mode=False
    )

    mock_boto_client = MagicMock()
    mock_boto_client.invoke_endpoint.side_effect = ClientError(
        {"Error": {"Code": "ModelError", "Message": "CUDA out of memory in worker 0"}},
        "InvokeEndpoint",
    )
    adapter._client = mock_boto_client

    with pytest.raises(SageMakerInvocationError) as exc_info:
        adapter.invoke_endpoint({"message": "Analyze"})
    assert "Model execution error" in str(exc_info.value)
    assert "CUDA out of memory" in str(exc_info.value)


def test_sagemaker_real_mode_timeout_handled():
    """ReadTimeoutError during invocation must raise SageMakerInvocationError."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-production-flood-endpoint", mock_mode=False
    )

    mock_boto_client = MagicMock()
    mock_boto_client.invoke_endpoint.side_effect = ReadTimeoutError(
        endpoint_url="https://runtime.sagemaker.ap-south-1.amazonaws.com"
    )
    adapter._client = mock_boto_client

    with pytest.raises(SageMakerInvocationError) as exc_info:
        adapter.invoke_endpoint({"message": "Analyze"})
    assert "timed out" in str(exc_info.value).lower()


def test_sagemaker_real_mode_connection_error_handled():
    """EndpointConnectionError must raise SageMakerInvocationError."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-production-flood-endpoint",
        region_name="ap-south-1",
        mock_mode=False,
    )

    mock_boto_client = MagicMock()
    mock_boto_client.invoke_endpoint.side_effect = EndpointConnectionError(
        endpoint_url="https://runtime.sagemaker.ap-south-1.amazonaws.com"
    )
    adapter._client = mock_boto_client

    with pytest.raises(SageMakerInvocationError) as exc_info:
        adapter.invoke_endpoint({"message": "Analyze"})
    assert "Could not connect to SageMaker endpoint" in str(exc_info.value)


def test_sagemaker_real_mode_malformed_non_json_response():
    """Non-JSON response from endpoint must be rejected and raise SageMakerInvocationError."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-production-flood-endpoint", mock_mode=False
    )

    mock_boto_client = MagicMock()
    mock_body = MagicMock()
    mock_body.read.return_value = b"<html>502 Bad Gateway</html>"
    mock_boto_client.invoke_endpoint.return_value = {"Body": mock_body}
    adapter._client = mock_boto_client

    with pytest.raises(SageMakerInvocationError) as exc_info:
        adapter.invoke_endpoint({"message": "Analyze"})
    assert "non-JSON" in str(exc_info.value)


def test_sagemaker_real_mode_empty_response_body():
    """Empty response body from endpoint must raise SageMakerInvocationError."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-production-flood-endpoint", mock_mode=False
    )

    mock_boto_client = MagicMock()
    mock_body = MagicMock()
    mock_body.read.return_value = b""
    mock_boto_client.invoke_endpoint.return_value = {"Body": mock_body}
    adapter._client = mock_boto_client

    with pytest.raises(SageMakerInvocationError) as exc_info:
        adapter.invoke_endpoint({"message": "Analyze"})
    assert "empty response body" in str(exc_info.value)


def test_real_mode_never_falls_back_to_mock():
    """Real mode (mock_mode=False) must NEVER return mock results even when errors occur."""
    adapter = SageMakerInferenceAdapter(
        endpoint_name="real-production-flood-endpoint", mock_mode=False
    )

    mock_boto_client = MagicMock()
    mock_boto_client.invoke_endpoint.side_effect = Exception("Generic network drop")
    adapter._client = mock_boto_client

    with pytest.raises(SageMakerInvocationError):
        # Must raise SageMakerInvocationError, NEVER return a dict with {"is_mock": True}
        adapter.invoke_endpoint({"message": "Analyze"})
