import os
import json
import logging
from typing import Optional, List, Any
import boto3
from botocore.exceptions import ClientError

from app.db.base_repository import IncidentRepositoryBase
from app.models.incident import Incident
from app.core.enums import IncidentStatus
from app.core.config import settings
from app.core.exceptions import (
    IncidentNotFoundError,
    InvalidStateTransitionError,
    TaskAlreadyExistsError
)

logger = logging.getLogger(__name__)

class DynamoDbIncidentRepository(IncidentRepositoryBase):
    """Production-grade Amazon DynamoDB repository implementation for Monsoon Sentinel incidents.
    Features conditional writes for race condition prevention, atomic transitions,
    and task dispatch idempotency.
    """

    def __init__(
        self,
        table_name: Optional[str] = None,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        dynamodb_resource: Optional[Any] = None
    ):
        self.table_name = table_name or settings.DYNAMODB_TABLE_NAME
        self.region_name = region_name or settings.AWS_REGION
        self.endpoint_url = endpoint_url or settings.DYNAMODB_ENDPOINT_URL

        if dynamodb_resource is not None:
            self._dynamodb = dynamodb_resource
        else:
            kwargs = {"region_name": self.region_name}
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url
            self._dynamodb = boto3.resource("dynamodb", **kwargs)

        self._table = self._dynamodb.Table(self.table_name)

    def _ensure_table_exists(self):
        """Helper to create table schema if running in local emulator or mock environment.
        Compatible with existing ProjectTable schema: partition key 'pk', sort key 'sk'.
        """
        try:
            self._table.load()
        except ClientError as e:
            if e.response["Error"]["Code"] in ["ResourceNotFoundException", "404"]:
                # Create table with pk (HASH) and sk (RANGE)
                self._dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {"AttributeName": "pk", "KeyType": "HASH"},
                        {"AttributeName": "sk", "KeyType": "RANGE"}
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "pk", "AttributeType": "S"},
                        {"AttributeName": "sk", "AttributeType": "S"}
                    ],
                    BillingMode="PAY_PER_REQUEST"
                )
                self._table = self._dynamodb.Table(self.table_name)
            else:
                raise

    def _make_key(self, incident_id: str) -> dict:
        return {
            "pk": f"INCIDENT#{incident_id}",
            "sk": "METADATA"
        }

    def get(self, incident_id: str) -> Optional[Incident]:
        try:
            response = self._table.get_item(Key=self._make_key(incident_id))
            item = response.get("Item")
            if item and "data_json" in item:
                return Incident.model_validate_json(item["data_json"])
            return None
        except ClientError as e:
            logger.error(f"DynamoDB get_item error for {incident_id}: {e}")
            raise

    def list_all(self) -> List[Incident]:
        incidents = []
        try:
            scan_kwargs = {}
            while True:
                response = self._table.scan(**scan_kwargs)
                for item in response.get("Items", []):
                    # Filter for incident records (pk begins with INCIDENT# and sk == METADATA)
                    pk = item.get("pk", "")
                    sk = item.get("sk", "")
                    if (pk.startswith("INCIDENT#") or item.get("incident_id")) and "data_json" in item:
                        incidents.append(Incident.model_validate_json(item["data_json"]))
                
                last_key = response.get("LastEvaluatedKey")
                if not last_key:
                    break
                scan_kwargs["ExclusiveStartKey"] = last_key

            # Sort descending by created_at
            incidents.sort(key=lambda x: x.created_at, reverse=True)
            return incidents
        except ClientError as e:
            logger.error(f"DynamoDB list_all scan error: {e}")
            raise

    def _build_item(self, incident: Incident) -> dict:
        key = self._make_key(incident.id)
        return {
            "pk": key["pk"],
            "sk": key["sk"],
            "incident_id": incident.id,
            "status": incident.status.value,
            "ward_id": incident.report.ward_id,
            "created_at": incident.created_at.isoformat(),
            "updated_at": incident.updated_at.isoformat(),
            "has_active_task": bool(incident.response_task is not None),
            "data_json": incident.model_dump_json()
        }

    def save(self, incident: Incident) -> Incident:
        item = self._build_item(incident)
        try:
            self._table.put_item(Item=item)
            return incident
        except ClientError as e:
            logger.error(f"DynamoDB save put_item error for {incident.id}: {e}")
            raise

    def save_transition(self, incident: Incident, expected_current_status: IncidentStatus) -> Incident:
        """Atomically persist state transition with conditional write ensuring
        attribute_exists(pk) AND #st = :expected_st.
        """
        item = self._build_item(incident)
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_exists(pk) AND #st = :expected_st",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={":expected_st": expected_current_status.value}
            )
            return incident
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                existing = self.get(incident.id)
                if not existing:
                    raise IncidentNotFoundError(incident.id)
                raise InvalidStateTransitionError(
                    current_status=existing.status.value,
                    target_status=incident.status.value,
                    reason=f"DynamoDB conditional check failed: current status '{existing.status.value}' does not match expected '{expected_current_status.value}'."
                )
            raise

    def save_task_dispatch(self, incident: Incident) -> Incident:
        """Atomically persist response task dispatch ensuring
        attribute_exists(pk) AND (#has_task = :false_val OR attribute_not_exists(has_active_task)).
        """
        item = self._build_item(incident)
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_exists(pk) AND (#has_task = :false_val OR attribute_not_exists(has_active_task))",
                ExpressionAttributeNames={"#has_task": "has_active_task"},
                ExpressionAttributeValues={":false_val": False}
            )
            return incident
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                existing = self.get(incident.id)
                if not existing:
                    raise IncidentNotFoundError(incident.id)
                if existing.response_task is not None:
                    raise TaskAlreadyExistsError(incident.id, existing.response_task.task_id)
            raise

    def delete(self, incident_id: str) -> bool:
        try:
            self._table.delete_item(Key=self._make_key(incident_id))
            return True
        except ClientError as e:
            logger.error(f"DynamoDB delete_item error for {incident_id}: {e}")
            return False

    def find_active(self) -> List[Incident]:
        all_incidents = self.list_all()
        terminal = [
            IncidentStatus.RESOLVED,
            IncidentStatus.VERIFIED,
            IncidentStatus.REJECTED,
            IncidentStatus.CANCELLED
        ]
        return [i for i in all_incidents if i.status not in terminal]
