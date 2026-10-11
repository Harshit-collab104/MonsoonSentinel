from typing import Optional
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field

from app.services.s3_storage import get_s3_storage, FileValidationError
from app.services.incident_service import IncidentService
from app.core.exceptions import IncidentNotFoundError

router = APIRouter(prefix="/evidence", tags=["evidence"])
service = IncidentService()

class EvidenceUploadJsonRequest(BaseModel):
    filename: str = Field(..., min_length=1)
    content_base64: str = Field(..., min_length=1)
    content_type: str = Field("image/jpeg")
    attach_to_task: bool = Field(False)

@router.post("/upload/{incident_id}")
async def upload_evidence_multipart(
    incident_id: str,
    file: UploadFile = File(...),
    attach_to_task: bool = Form(False)
):
    """Uploads private photographic evidence to S3 and attaches the S3 key to the incident record."""
    try:
        inc = service._get_or_raise(incident_id)
        file_bytes = await file.read()
        s3 = get_s3_storage()

        result = s3.upload_evidence(
            file_bytes=file_bytes,
            filename=file.filename or "evidence.jpg",
            incident_id=incident_id,
            content_type=file.content_type or "image/jpeg"
        )

        presigned_url = s3.generate_presigned_url(result["s3_key"])

        # Attach S3 key reference to incident record
        if attach_to_task and inc.response_task:
            inc.response_task.evidence_url = result["s3_key"]
        else:
            inc.report.image_url = result["s3_key"]
        
        service.repo.save(inc)

        return {
            "incident_id": incident_id,
            "s3_key": result["s3_key"],
            "s3_uri": result["s3_uri"],
            "presigned_view_url": presigned_url,
            "size_bytes": result["size_bytes"]
        }
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload error: {str(e)}")

@router.post("/upload-json/{incident_id}")
def upload_evidence_json(
    incident_id: str,
    payload: EvidenceUploadJsonRequest
):
    """Uploads base64-encoded evidence to S3."""
    try:
        inc = service._get_or_raise(incident_id)
        try:
            file_bytes = base64.b64decode(payload.content_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 payload")

        s3 = get_s3_storage()
        result = s3.upload_evidence(
            file_bytes=file_bytes,
            filename=payload.filename,
            incident_id=incident_id,
            content_type=payload.content_type
        )

        presigned_url = s3.generate_presigned_url(result["s3_key"])

        if payload.attach_to_task and inc.response_task:
            inc.response_task.evidence_url = result["s3_key"]
        else:
            inc.report.image_url = result["s3_key"]

        service.repo.save(inc)

        return {
            "incident_id": incident_id,
            "s3_key": result["s3_key"],
            "s3_uri": result["s3_uri"],
            "presigned_view_url": presigned_url,
            "size_bytes": result["size_bytes"]
        }
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload error: {str(e)}")

@router.get("/presigned-url")
def get_presigned_url(
    s3_key: str = Query(..., min_length=1, description="S3 object key"),
    expires_in: int = Query(3600, ge=60, le=86400, description="Expiration seconds")
):
    """Generates a secure, time-limited presigned GET URL for private evidence inspection."""
    clean_key = s3_key.strip().strip('"').strip("'").lstrip("/")
    try:
        s3 = get_s3_storage()
        url = s3.generate_presigned_url(clean_key, expires_in_seconds=expires_in)
        return {"s3_key": clean_key, "presigned_url": url, "expires_in_seconds": expires_in}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Presigned URL generation error: {str(e)}")
