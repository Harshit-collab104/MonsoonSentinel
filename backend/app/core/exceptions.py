class IncidentError(Exception):
    """Base exception for incident domain errors."""
    pass

class InvalidStateTransitionError(IncidentError):
    """Raised when an illegal lifecycle transition is attempted."""
    def __init__(self, current_status: str, target_status: str, reason: str = ""):
        super().__init__(f"Cannot transition from {current_status} to {target_status}. {reason}".strip())
        self.current_status = current_status
        self.target_status = target_status
        self.reason = reason

class IncidentNotFoundError(IncidentError):
    def __init__(self, incident_id: str):
        super().__init__(f"Incident '{incident_id}' not found.")
        self.incident_id = incident_id

class TaskAlreadyExistsError(IncidentError):
    def __init__(self, incident_id: str, existing_task_id: str):
        super().__init__(f"Incident '{incident_id}' already has an active response task '{existing_task_id}'. Duplicate dispatch prevented.")
        self.incident_id = incident_id
        self.existing_task_id = existing_task_id

class VerificationFailedError(IncidentError):
    def __init__(self, incident_id: str, reason: str):
        super().__init__(f"Verification failed for incident '{incident_id}': {reason}")
        self.incident_id = incident_id
        self.reason = reason

class SageMakerConfigurationError(IncidentError):
    """Raised when real SageMaker inference is enabled but the endpoint is misconfigured."""
    def __init__(self, message: str):
        super().__init__(message)

class SageMakerInvocationError(IncidentError):
    """Raised when real SageMaker model endpoint invocation fails or times out."""
    def __init__(self, endpoint_name: str, message: str):
        super().__init__(f"SageMaker endpoint '{endpoint_name}' invocation failed: {message}")
        self.endpoint_name = endpoint_name
