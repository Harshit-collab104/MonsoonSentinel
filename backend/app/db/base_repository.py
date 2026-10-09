from abc import ABC, abstractmethod
from typing import Optional, List
from app.models.incident import Incident
from app.core.enums import IncidentStatus

class IncidentRepositoryBase(ABC):
    """Abstract repository interface for incident storage.
    Can be backed by SQLite/JSON locally, or DynamoDB in AWS deployment.
    """

    @abstractmethod
    def get(self, incident_id: str) -> Optional[Incident]:
        """Retrieve an incident by ID."""
        pass

    @abstractmethod
    def list_all(self) -> List[Incident]:
        """List all incidents."""
        pass

    @abstractmethod
    def save(self, incident: Incident) -> Incident:
        """Create or update an incident unconditionally."""
        pass

    @abstractmethod
    def delete(self, incident_id: str) -> bool:
        """Delete an incident by ID."""
        pass

    @abstractmethod
    def find_active(self) -> List[Incident]:
        """List incidents that are not in terminal states (RESOLVED, VERIFIED, REJECTED, CANCELLED)."""
        pass

    @abstractmethod
    def save_transition(self, incident: Incident, expected_current_status: IncidentStatus) -> Incident:
        """Atomically persist state transition, ensuring the record's current status matches expected_current_status.
        Raises InvalidStateTransitionError if condition fails.
        """
        pass

    @abstractmethod
    def save_task_dispatch(self, incident: Incident) -> Incident:
        """Atomically persist response task dispatch, ensuring no active response task already exists.
        Raises TaskAlreadyExistsError if task already exists.
        """
        pass
