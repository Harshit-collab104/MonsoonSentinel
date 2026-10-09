import os
import uuid
import json
import logging
from typing import Optional, Dict, Any, Union
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)

class FileValidationError(Exception):
    """Raised when an uploaded evidence file fails size or type validation."""
    pass

class S3StorageService:
    """Manages private Amazon S3 storage for Monsoon Sentinel.
    Handles incident photographic evidence, telemetry records, and municipal flood datasets.
    Enforces server-side encryption, private access, file type and size validation,
    and time-limited presigned URL generation.
    """

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
    ALLOWED_MIME_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf"
    }
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        s3_client: Optional[Any] = None
    ):
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.region_name = region_name or settings.AWS_REGION
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT_URL

        if s3_client is not None:
            self._s3 = s3_client
        else:
            kwargs = {"region_name": self.region_name}
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url
            self._s3 = boto3.client("s3", **kwargs)

    def _ensure_bucket_exists(self):
        """Helper to create private bucket with encryption and public access block if testing locally."""
        try:
            self._s3.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] in ["404", "NoSuchBucket"]:
                create_kwargs = {"Bucket": self.bucket_name}
                if self.region_name != "us-east-1":
                    create_kwargs["CreateBucketConfiguration"] = {
                        "LocationConstraint": self.region_name
                    }
                self._s3.create_bucket(**create_kwargs)

                # Enable Block Public Access
                self._s3.put_public_access_block(
                    Bucket=self.bucket_name,
                    PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True,
                        "RestrictPublicBuckets": True
                    }
                )

                # Enable Default Server-Side Encryption (AES256)
                self._s3.put_bucket_encryption(
                    Bucket=self.bucket_name,
                    ServerSideEncryptionConfiguration={
                        "Rules": [
                            {
                                "ApplyServerSideEncryptionByDefault": {
                                    "SSEAlgorithm": "AES256"
                                }
                            }
                        ]
                    }
                )
            else:
                raise

    def validate_file(self, filename: str, file_bytes: bytes, content_type: Optional[str] = None):
        """Validates file extension, MIME type, and maximum file size."""
        # Check size
        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise FileValidationError(
                f"File size exceeds maximum limit of 5 MB ({len(file_bytes)} bytes provided)."
            )

        # Check extension
        _, ext = os.path.splitext(filename.lower())
        if ext not in self.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"File extension '{ext}' is not permitted. Allowed: {sorted(list(self.ALLOWED_EXTENSIONS))}"
            )

        # Check MIME type if provided
        if content_type and content_type.lower() not in self.ALLOWED_MIME_TYPES:
            raise FileValidationError(
                f"MIME type '{content_type}' is not allowed for evidence uploads."
            )

    def upload_evidence(
        self,
        file_bytes: bytes,
        filename: str,
        incident_id: str,
        content_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """Uploads private incident evidence file to S3 with AES256 encryption.
        Returns S3 object key and metadata without embedding raw bytes.
        """
        self.validate_file(filename, file_bytes, content_type)

        clean_filename = os.path.basename(filename)
        unique_id = uuid.uuid4().hex[:8]
        s3_key = f"evidence/{incident_id}/{unique_id}_{clean_filename}"

        try:
            self._s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type,
                ServerSideEncryption="AES256",
                Metadata={
                    "incident_id": incident_id,
                    "original_filename": clean_filename
                }
            )

            return {
                "bucket": self.bucket_name,
                "s3_key": s3_key,
                "s3_uri": f"s3://{self.bucket_name}/{s3_key}",
                "size_bytes": len(file_bytes),
                "content_type": content_type
            }
        except ClientError as e:
            logger.error(f"Failed to upload evidence to S3 for {incident_id}: {e}")
            raise

    def generate_presigned_url(self, s3_key: str, expires_in_seconds: int = 3600) -> str:
        """Generates a secure, time-limited presigned GET URL for private evidence inspection."""
        try:
            url = self._s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expires_in_seconds
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            raise

    def upload_dataset(self, dataset_name: str, data: Union[str, bytes, dict]) -> str:
        """Stores municipal seed datasets, radar baselines, or drainage models in S3."""
        s3_key = f"datasets/{dataset_name}.json"
        body_bytes = json.dumps(data).encode("utf-8") if isinstance(data, dict) else (
            data.encode("utf-8") if isinstance(data, str) else data
        )

        try:
            self._s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=body_bytes,
                ContentType="application/json",
                ServerSideEncryption="AES256"
            )
            return s3_key
        except ClientError as e:
            logger.error(f"Failed to upload dataset {dataset_name} to S3: {e}")
            raise

    def get_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """Retrieves a municipal dataset from S3."""
        s3_key = f"datasets/{dataset_name}.json"
        try:
            response = self._s3.get_object(Bucket=self.bucket_name, Key=s3_key)
            raw = response["Body"].read().decode("utf-8")
            return json.loads(raw)
        except ClientError as e:
            logger.error(f"Failed to retrieve dataset {dataset_name} from S3: {e}")
            raise

_s3_storage_service: Optional[S3StorageService] = None

def get_s3_storage() -> S3StorageService:
    global _s3_storage_service
    if _s3_storage_service is None:
        _s3_storage_service = S3StorageService()
    return _s3_storage_service
