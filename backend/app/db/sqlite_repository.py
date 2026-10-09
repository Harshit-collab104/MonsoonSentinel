import sqlite3
import threading
from typing import Optional, List
from app.db.base_repository import IncidentRepositoryBase
from app.models.incident import Incident
from app.core.enums import IncidentStatus
from app.core.exceptions import (
    IncidentNotFoundError,
    InvalidStateTransitionError,
    TaskAlreadyExistsError
)

class SqliteIncidentRepository(IncidentRepositoryBase):
    """Thread-safe SQLite incident repository implementation storing incidents as JSON documents."""

    def __init__(self, db_path: str = "monsoon_sentinel.db"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incidents (
                        id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        ward_id TEXT NOT NULL,
                        data_json TEXT NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_ward ON incidents(ward_id)")
                conn.commit()

    def get(self, incident_id: str) -> Optional[Incident]:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT data_json FROM incidents WHERE id = ?", (incident_id,))
                row = cursor.fetchone()
                if row:
                    return Incident.model_validate_json(row["data_json"])
                return None

    def list_all(self) -> List[Incident]:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT data_json FROM incidents ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [Incident.model_validate_json(r["data_json"]) for r in rows]

    def save(self, incident: Incident) -> Incident:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO incidents (id, status, created_at, updated_at, ward_id, data_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        status = excluded.status,
                        updated_at = excluded.updated_at,
                        ward_id = excluded.ward_id,
                        data_json = excluded.data_json
                """, (
                    incident.id,
                    incident.status.value,
                    incident.created_at.isoformat(),
                    incident.updated_at.isoformat(),
                    incident.report.ward_id,
                    incident.model_dump_json()
                ))
                conn.commit()
                return incident

    def save_transition(self, incident: Incident, expected_current_status: IncidentStatus) -> Incident:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT status FROM incidents WHERE id = ?", (incident.id,))
                row = cursor.fetchone()
                if not row:
                    raise IncidentNotFoundError(incident.id)
                current_db_status = row["status"]
                if current_db_status != expected_current_status.value:
                    raise InvalidStateTransitionError(
                        current_status=current_db_status,
                        target_status=incident.status.value,
                        reason=f"Current status {current_db_status} does not match expected {expected_current_status.value}"
                    )
                return self.save(incident)

    def save_task_dispatch(self, incident: Incident) -> Incident:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT data_json FROM incidents WHERE id = ?", (incident.id,))
                row = cursor.fetchone()
                if not row:
                    raise IncidentNotFoundError(incident.id)
                existing = Incident.model_validate_json(row["data_json"])
                if existing.response_task is not None:
                    raise TaskAlreadyExistsError(incident.id, existing.response_task.task_id)
                return self.save(incident)

    def delete(self, incident_id: str) -> bool:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
                conn.commit()
                return cursor.rowcount > 0

    def find_active(self) -> List[Incident]:
        terminal_statuses = [
            IncidentStatus.RESOLVED.value,
            IncidentStatus.VERIFIED.value,
            IncidentStatus.REJECTED.value,
            IncidentStatus.CANCELLED.value
        ]
        with self._lock:
            with self._get_connection() as conn:
                placeholders = ",".join("?" for _ in terminal_statuses)
                cursor = conn.execute(
                    f"SELECT data_json FROM incidents WHERE status NOT IN ({placeholders}) ORDER BY created_at DESC",
                    terminal_statuses
                )
                rows = cursor.fetchall()
                return [Incident.model_validate_json(r["data_json"]) for r in rows]

# Global singleton instance for local runtime
_default_repo: Optional[IncidentRepositoryBase] = None

def get_repository(db_path: Optional[str] = None) -> IncidentRepositoryBase:
    global _default_repo
    if _default_repo is None or db_path is not None:
        from app.core.config import settings
        if settings.STORAGE_BACKEND == "dynamodb":
            from app.db.dynamodb_repository import DynamoDbIncidentRepository
            _default_repo = DynamoDbIncidentRepository()
        else:
            path = db_path or settings.DATABASE_PATH
            _default_repo = SqliteIncidentRepository(path)
    return _default_repo
