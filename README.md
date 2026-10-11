# Monsoon Sentinel — AI-Assisted Urban Waterlogging Risk & Response System
**Production AWS Serverless Persistence & Cloud Architecture**

---

## Overview

**Monsoon Sentinel** is an AI-assisted urban disaster response and flood risk mitigation system designed for municipal municipal corporations. During heavy monsoon events, rapid surface runoff, clogged storm culverts, and delayed dispatch lead to severe urban waterlogging, transit paralyzation, and property loss.

### AWS Persistence & Cloud Architecture
- **Serverless API Runtime**: Containerized FastAPI application running on **AWS Lambda** via **Mangum** and **Amazon API Gateway** (Regional `/Prod` stage).
- **Pluggable Persistence**: Switch between **SQLite/JSON** (local default) and **Amazon DynamoDB** (`ProjectTable`) via `STORAGE_BACKEND="sqlite" | "dynamodb"`.
- **Atomic Concurrency & Idempotency**: DynamoDB conditional writes enforce valid state transitions (`#status = :expected_status`) and prevent duplicate response task dispatches directly at the database engine level.
- **Private Amazon S3 Storage**: Photographic evidence and municipal flood datasets are stored privately in encrypted S3 bucket (`project-evidence-a7k29x`) with Public Access Block enabled. Access is granted exclusively through short-lived presigned URLs.
- **Production Frontend**: React 19 SPA bundled with Vite 8 and hosted globally via **AWS Amplify Hosting**.
- **Infrastructure as Code**: AWS SAM template ([`template.yaml`](template.yaml)) defining the Lambda function, API Gateway, DynamoDB IAM policies, and S3 lifecycle configurations.

---

## Technology Stack

- **Backend**: Python 3.12/3.14+, FastAPI, Mangum, Uvicorn, Pydantic v2, Boto3, Moto
- **Agent Orchestration**: **Strands Agents SDK** (`strands-agents 1.54.0`)
- **Model Inference**: **Amazon SageMaker AI** (abstracted behind `SageMakerInferenceAdapter`, running in local mock mode without cloud billing)
- **Database & Storage**:
  - **Amazon DynamoDB**: Table `ProjectTable` with partition key `incident_id` and GSI `StatusIndex`.
  - **Amazon S3**: Private bucket `project-evidence-a7k29x` with AES256 server-side encryption and Block Public Access.
  - **SQLite / JSON**: Local fallback repository implementing identical `IncidentRepositoryBase` contract.
- **Frontend**: React 19, Vite 8, Tailwind CSS v4, Leaflet GIS, Lucide Icons, Hosted on **AWS Amplify**
- **Testing**: Deterministic `pytest` unit test suite with `moto` local AWS emulation.

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

### Backend Environment Variables
| Variable | Default | Description |
|---|---|---|
| `STORAGE_BACKEND` | `dynamodb` | Persistence backend: `sqlite` for local development, `dynamodb` for AWS persistence |
| `DYNAMODB_TABLE_NAME` | `ProjectTable` | DynamoDB table name |
| `DYNAMODB_ENDPOINT_URL` | *(None)* | Optional custom endpoint URL (for DynamoDB Local emulator) |
| `S3_BUCKET_NAME` / `EVIDENCE_BUCKET` | `project-evidence-a7k29x` | S3 private bucket name for evidence and datasets |
| `S3_ENDPOINT_URL` | *(None)* | Optional custom endpoint URL (for MinIO or S3 local emulator) |
| `AWS_REGION` | `ap-south-1` | Target AWS region (e.g. `ap-south-1`) |
| `USE_MOCK_SAGEMAKER` | `true` | Mock adapter toggle (`true` avoids cloud billing during development & demo) |
| `SAGEMAKER_ENDPOINT_NAME` | `mock-monsoon-sagemaker-endpoint` | SageMaker AI endpoint name |
| `ROOT_PATH` | `/Prod` | Stage prefix for API Gateway deployment |

### Frontend Environment Variables
| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `""` | Deployed API Gateway URL (e.g. `https://<api-id>.execute-api.ap-south-1.amazonaws.com/Prod`). When empty, Vite dev server proxies to `http://localhost:8000`. |

---

## Deploying Frontend to AWS Amplify Hosting

The frontend repository includes preconfigured AWS Amplify build pipelines ([`amplify.yml`](amplify.yml) and [`frontend/amplify.yml`](frontend/amplify.yml)):

1. Open the **[AWS Amplify Console](https://ap-south-1.console.aws.amazon.com/amplify/home?region=ap-south-1)**.
2. Click **Create new app** > **Host web app**.
3. Connect your GitHub repository (`Harshit-collab104/MonsoonSentinel`) and select branch `main`.
4. Leave monorepo **unchecked** (Amplify will automatically use the root `amplify.yml`).
5. Under **Environment variables**, set:
   - `VITE_API_BASE_URL`: `https://<your-api-id>.execute-api.ap-south-1.amazonaws.com/Prod`
6. Click **Save and deploy**.
7. AWS Amplify will provision, build, and deploy your site to a public, secure `https://main.dXXXXXXXX.amplifyapp.com` endpoint.

---

## AWS SAM Backend Deployment

The backend serverless infrastructure is defined in [`template.yaml`](template.yaml).

### Build & Deploy:
```bash
# 1. Build the SAM template
sam build

# 2. Deploy to AWS
sam deploy --guided
```

### Inspect Output Endpoint:
```powershell
aws cloudformation describe-stacks `
  --stack-name monsoon-sentinel-dev `
  --region ap-south-1 `
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" `
  --output text
```

---

## Running Locally

### Step 1: Start Backend (Terminal 1)
```powershell
cd backend
python -m uvicorn app.api.main:app --port 8000 --reload
```

- API Documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/`

### Step 2: Start Frontend (Terminal 2)
```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.
