import pytest
import boto3
from moto import mock_aws

from app.services.s3_storage import S3StorageService, FileValidationError

@pytest.fixture
def s3_env():
    with mock_aws():
        svc = S3StorageService(
            bucket_name="monsoon-sentinel-evidence-test",
            region_name="ap-south-1"
        )
        svc._ensure_bucket_exists()
        yield svc

def test_s3_bucket_private_encryption(s3_env):
    s3_client = s3_env._s3
    bucket = s3_env.bucket_name

    # Check Public Access Block
    pab = s3_client.get_public_access_block(Bucket=bucket)
    config = pab["PublicAccessBlockConfiguration"]
    assert config["BlockPublicAcls"] is True
    assert config["IgnorePublicAcls"] is True
    assert config["BlockPublicPolicy"] is True
    assert config["RestrictPublicBuckets"] is True

    # Check Default Encryption
    enc = s3_client.get_bucket_encryption(Bucket=bucket)
    rules = enc["ServerSideEncryptionConfiguration"]["Rules"]
    assert rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"] == "AES256"

def test_s3_evidence_file_validation(s3_env):
    valid_bytes = b"fake image bytes content"

    # Valid upload
    res = s3_env.upload_evidence(
        file_bytes=valid_bytes,
        filename="drain_flood.jpg",
        incident_id="INC-EVID-01",
        content_type="image/jpeg"
    )
    assert res["bucket"] == s3_env.bucket_name
    assert "evidence/INC-EVID-01/" in res["s3_key"]
    assert res["s3_key"].endswith("drain_flood.jpg")

    # Invalid extension rejected
    with pytest.raises(FileValidationError):
        s3_env.upload_evidence(
            file_bytes=valid_bytes,
            filename="malicious_script.sh",
            incident_id="INC-EVID-01",
            content_type="application/x-sh"
        )

    # Exceeding 5 MB rejected
    large_bytes = b"0" * (5 * 1024 * 1024 + 10)
    with pytest.raises(FileValidationError):
        s3_env.upload_evidence(
            file_bytes=large_bytes,
            filename="oversized_drone_video.jpg",
            incident_id="INC-EVID-01"
        )

def test_s3_presigned_url_generation(s3_env):
    upload_res = s3_env.upload_evidence(
        file_bytes=b"sample evidence jpeg",
        filename="clearance_photo.png",
        incident_id="INC-EVID-02",
        content_type="image/png"
    )

    url = s3_env.generate_presigned_url(upload_res["s3_key"], expires_in_seconds=1800)
    assert url is not None
    assert upload_res["s3_key"] in url
    assert "AWSAccessKeyId=" in url or "X-Amz-Signature=" in url or "Signature=" in url

def test_s3_dataset_storage(s3_env):
    dataset_data = {
        "ward_atlas": "Bengaluru_Monsoon_2026",
        "chronic_hotspots": ["WARD-12", "WARD-07", "WARD-04"],
        "critical_culvert_count": 48
    }

    s3_key = s3_env.upload_dataset("hotspot_atlas", dataset_data)
    assert s3_key == "datasets/hotspot_atlas.json"

    retrieved = s3_env.get_dataset("hotspot_atlas")
    assert retrieved["ward_atlas"] == "Bengaluru_Monsoon_2026"
    assert len(retrieved["chronic_hotspots"]) == 3
