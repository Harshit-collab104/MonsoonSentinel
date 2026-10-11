# Monsoon Sentinel — AI-Assisted Urban Waterlogging Risk & Response System
**Phase 2: AWS Persistence (Amazon DynamoDB & Amazon S3)**

---

## Overview

**Monsoon Sentinel** is an AI-assisted urban disaster response and flood risk mitigation system designed for municipal municipal corporations. During heavy monsoon events, rapid surface runoff, clogged storm culverts, and delayed dispatch lead to severe urban waterlogging, transit paralyzation, and property loss.

### Phase 2 AWS Persistence Highlights
- **Pluggable Persistence**: Switch between **SQLite/JSON** (local default) and **Amazon DynamoDB** via `STORAGE_BACKEND="sqlite" | "dynamodb"`.
- **Atomic Concurrency & Idempotency**: DynamoDB conditional writes enforce valid state transitions (`#status = :expected_status`) and prevent duplicate response task dispatches directly at the database engine level.
- **Private Amazon S3 Storage**: Photographic evidence and municipal flood datasets are stored privately in encrypted S3 buckets with Public Access Block enabled. Access is granted exclusively through short-lived presigned URLs.
- **Infrastructure as Code**: AWS SAM template ([`template.yaml`](template.yaml)) defining the DynamoDB table with GSI and S3 private bucket.

---

## Technology Stack

- **Backend**: Python 3.14+, FastAPI, Uvicorn, Pydantic v2, Boto3, Moto
- **Agent Orchestration**: **Strands Agents SDK** (`strands-agents 1.54.0`)
- **Model Inference**: **Amazon SageMaker AI** (abstracted behind `SageMakerInferenceAdapter`, running in local mock mode without requiring AWS credentials or cloud billing)
- **Database & Storage**:
  - **Amazon DynamoDB**: Table `monsoon-sentinel-incidents` with partition key `incident_id` and GSI `StatusIndex`.
  - **Amazon S3**: Private bucket `monsoon-sentinel-evidence` with AES256 server-side encryption and Block Public Access.
  - **SQLite / JSON**: Local fallback repository implementing identical `IncidentRepositoryBase` contract.
- **Frontend**: React 19, Vite, Tailwind CSS, Lucide Icons, SVG/GIS Hydrological Grid
- **Testing**: Deterministic `pytest` unit test suite (30 passing tests) with `moto` local AWS emulation.

---

## Core 10-Step Workflow

```
[1. Citizen Report] ──> [2. Validate & Store] ──> [3. Environmental Telemetry]
                                                            │
[6. Strands Agent]  <── [5. Urgency Ranking]  <── [4. Deterministic Risk Engine]
        │
[7. Supervisor Review] ──> [8. Task Dispatch] ──> [9. Resolution Submission]
                                                            │
                                                  [10. Telemetry Verification]
                                                            │
                                                  [DynamoDB & S3 Persistence]
```

1. **Citizen Report**: A citizen submits a waterlogging or drain blockage report with GPS coordinates, ward, water depth, and blockage level.
2. **Validation & Storage**: The system validates input schemas and stores the incident in `NEW` status in DynamoDB or SQLite.
3. **Environmental Telemetry**: Rainfall radar, storm culvert capacity, historical flood records, and nearby incident density are retrieved.
4. **Deterministic Risk Calculation**: The Python risk engine computes an explainable risk score ($R \in [0, 100]$) and severity tier (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`). Missing data is flagged with an explicit uncertainty penalty.
5. **Urgency Prioritization**: The prioritization service scores and ranks active incidents based on depth, blockage severity, and report age.
6. **Agent Recommendation**: The Strands agent calls explicit tools to recommend required machinery (e.g. Super-Sucker Hydro-Vacuum rig, Mobile Dewatering pumps, or Desilting crews).
7. **Human Supervisor Review**: A municipal dispatcher approves or rejects the recommendation in the Human Approval Queue.
8. **Response Task Dispatch**: Approval dispatches a response task (`IN_PROGRESS`). Database-level conditional writes strictly prevent duplicate dispatch orders. Dispatches explicitly state physical drain clearance is ongoing.
9. **Resolution Update**: Field teams record completed clearance notes and photographic evidence uploaded to private S3 bucket (`RESOLVED`).
10. **Telemetry Verification**: Culvert flow rate ($> 20\text{ LPS}$) and residual depth ($< 5\text{ cm}$) are verified. Successful checks transition to `VERIFIED`; failed checks transition to `NEEDS_HUMAN_REVIEW`.

---

## Configuration & Environment Variables

Configure application behavior using environment variables (never commit credentials or `.env` secrets):

| Variable | Default | Description |
|---|---|---|
| `STORAGE_BACKEND` | `sqlite` | Persistence backend: `sqlite` for local development, `dynamodb` for AWS persistence |
| `DYNAMODB_TABLE_NAME` | `monsoon-sentinel-incidents` | DynamoDB table name |
| `DYNAMODB_ENDPOINT_URL` | *(None)* | Optional custom endpoint URL (for DynamoDB Local emulator) |
| `S3_BUCKET_NAME` | `monsoon-sentinel-evidence` | S3 private bucket name for evidence and datasets |
| `S3_ENDPOINT_URL` | *(None)* | Optional custom endpoint URL (for MinIO or S3 local emulator) |
| `AWS_REGION` | `ap-south-1` | Target AWS region (e.g. `ap-south-1`, `us-east-1`) |
| `USE_MOCK_SAGEMAKER` | `true` | Mock adapter toggle (`true` avoids cloud billing during development) |
| `SAGEMAKER_ENDPOINT_NAME` | `mock-monsoon-sagemaker-endpoint` | SageMaker AI endpoint name |

---

## Required IAM Permissions

For security, the application adheres to the principle of least privilege. Do not use `AdministratorAccess`.

### 1. Application Execution Role Policy
Attach this policy to the Lambda execution role or ECS task role running Monsoon Sentinel:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBIncidentsAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/monsoon-sentinel-incidents",
        "arn:aws:dynamodb:*:*:table/monsoon-sentinel-incidents/index/*"
      ]
    },
    {
      "Sid": "S3EvidencePrivateAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:HeadBucket",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::monsoon-sentinel-evidence*",
        "arn:aws:s3:::monsoon-sentinel-evidence*/*"
      ]
    }
  ]
}
```

### 2. Developer / Deployment Identity Policy (SAM / CloudFormation)
The developer identity executing SAM deployments requires permissions to manage CloudFormation stacks, DynamoDB tables, and S3 buckets:
- `cloudformation:*` on stack `monsoon-sentinel-*`
- `dynamodb:CreateTable`, `dynamodb:DescribeTable`, `dynamodb:UpdateTable`, `dynamodb:DeleteTable`, `dynamodb:TagResource`
- `s3:CreateBucket`, `s3:PutBucketPublicAccessBlock`, `s3:PutBucketEncryption`, `s3:PutBucketVersioning`, `s3:PutLifecycleConfiguration`, `s3:DeleteBucket`

---

## AWS SAM Infrastructure Deployment

The infrastructure is defined in [`template.yaml`](template.yaml).

### Build & Deploy with AWS SAM:
```bash
# 1. Build the SAM template
sam build

# 2. Deploy infrastructure interactively (guided)
sam deploy --guided \
  --stack-name monsoon-sentinel-infra \
  --region ap-south-1 \
  --parameter-overrides Environment=dev DynamoDBTableName=monsoon-sentinel-incidents EvidenceBucketPrefix=monsoon-sentinel-evidence
```

### Infrastructure Cleanup (Teardown):
To delete the deployed resources and avoid cloud billing:
```bash
# Delete SAM stack
sam delete --stack-name monsoon-sentinel-infra --region ap-south-1
```

---

## Automated Test Execution

All tests run locally using `moto` AWS emulation and SQLite. No live AWS credentials or cloud costs are incurred.

```bash
# Run the complete test suite (30 passing tests)
python -m pytest -v
```

### Test Coverage Breakdown:
- `test_repository_contract.py`: Parametrized contract test asserting identical semantics and query behavior across both SQLite and DynamoDB implementations.
- `test_dynamodb_repository.py`: Tests DynamoDB storage, conditional transitions, duplicate task dispatch prevention, and persistence across simulated application restarts.
- `test_s3_storage.py`: Tests S3 private bucket creation, Block Public Access, AES256 encryption, file type validation (accepts PNG/JPG/PDF, rejects scripts), 5MB size limit, and presigned URLs.
- `test_aws_workflow.py`: End-to-end 10-step municipal flood workflow test backed entirely by DynamoDB and S3.
- `test_risk_engine.py`: Deterministic scoring formulas and missing data uncertainty penalties.
- `test_prioritization.py`: Urgency ranking across multi-incident queues.
- `test_lifecycle.py`: State machine progression and illegal transition guards.
- `test_idempotency.py`: Task dispatch idempotency guards.
- `test_verification.py`: Telemetry verification outcomes (`VERIFIED` vs `NEEDS_HUMAN_REVIEW`).
- `test_api_workflow.py`: Full FastAPI integration test.

---

## Running the Application Locally

### Step 1: Start Backend (Terminal 1)
```powershell
cd backend
python -m uvicorn app.api.main:app --port 8000 --reload
```
To run backend with DynamoDB (connecting to local DynamoDB or AWS):
```powershell
set STORAGE_BACKEND=dynamodb
set DYNAMODB_TABLE_NAME=monsoon-sentinel-incidents
python -m uvicorn app.api.main:app --port 8000 --reload
```

- API Documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/`

### Step 2: Start Frontend (Terminal 2)
```powershell
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.
