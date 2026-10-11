import os
from typing import Optional

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Monsoon Sentinel"
    API_V1_PREFIX: str = "/api/v1"

    # Storage Backend Selection: "sqlite" (default local) or "dynamodb"
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "dynamodb").lower()
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "monsoon_sentinel.db")

    # AWS DynamoDB Configuration
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "ProjectTable")
    DYNAMODB_ENDPOINT_URL: Optional[str] = os.getenv("DYNAMODB_ENDPOINT_URL", None)

    # AWS S3 Configuration
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", os.getenv("EVIDENCE_BUCKET", "project-evidence-a7k29x"))
    S3_ENDPOINT_URL: Optional[str] = os.getenv("S3_ENDPOINT_URL", None)

    # AWS General Configuration
    AWS_REGION: str = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "ap-south-1"

    # Deployment environment and API Gateway stage prefix (e.g. "/Prod")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev").lower()
    ROOT_PATH: str = os.getenv("ROOT_PATH", "/Prod" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "")

    # SageMaker AI Mock Adapter Toggle
    USE_MOCK_SAGEMAKER: bool = os.getenv("USE_MOCK_SAGEMAKER", "true").lower() == "true"
    SAGEMAKER_ENDPOINT_NAME: str = os.getenv("SAGEMAKER_ENDPOINT_NAME", "mock-monsoon-sagemaker-endpoint")

settings = Settings()
