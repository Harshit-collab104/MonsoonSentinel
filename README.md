# Monsoon Sentinel — AI-Assisted Urban Waterlogging Risk & Response System
**Phase 1: Local MVP (Ship It Track)**

---

## Overview

**Monsoon Sentinel** is an AI-assisted urban disaster response and flood risk mitigation system designed for municipal municipal corporations. During heavy monsoon events, rapid surface runoff, clogged storm culverts, and delayed dispatch lead to severe urban waterlogging, transit paralyzation, and property loss.

Monsoon Sentinel provides:
1. **Intake & Spatial Correlation**: Citizen-reported drain blockages combined with real-time rain gauge telemetry, drainage capacity models, and historical waterlogging hotspots.
2. **Deterministic Risk Engine**: Mathematical, explainable risk scoring ($R \in [0, 100]$) and urgency prioritization. AI models **never invent sensor measurements or determine risk scores directly**.
3. **Strands Agent Orchestration**: Autonomous triage calling 12 narrowly scoped tools to evaluate risk, prioritize incidents, and formulate operational equipment recommendations.
4. **Human-in-the-Loop Authorization**: Dedicated supervisor approval queue preventing accidental dispatches or hallucinated field actions. Dispatches strictly state that physical drain clearance has *not* occurred yet.
5. **Resolution Verification & Auditability**: Telemetry-driven drainage validation (LPS flow rate and residual water depth) with immutable audit history tracking actor, action, timestamp, and rationale.

---

## Technology Stack

- **Backend**: Python 3.14+, FastAPI, Uvicorn, Pydantic v2
- **Agent Orchestration**: **Strands Agents SDK** (`strands-agents 1.54.0`)
- **Model Inference**: **Amazon SageMaker AI** (abstracted behind `SageMakerInferenceAdapter`, running in local mock mode without requiring AWS credentials or cloud billing)
- **Local Persistence**: SQLite JSON repository behind `IncidentRepositoryBase` (architected for 1-to-1 replacement with **Amazon DynamoDB** in Phase 2)
- **Frontend**: React 19, Vite, Tailwind CSS, Lucide Icons, SVG/GIS Hydrological Grid
- **Testing**: Deterministic `pytest` unit test suite and end-to-end API integration tests

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
                                                  [Audit History Stored]
```

1. **Citizen Report**: A citizen submits a waterlogging or drain blockage report with GPS coordinates, ward, water depth, and blockage level.
2. **Validation & Storage**: The system validates input schemas and stores the incident in `NEW` status.
3. **Environmental Telemetry**: Rainfall radar, storm culvert capacity, historical flood records, and nearby incident density are retrieved.
4. **Deterministic Risk Calculation**: The Python risk engine computes an explainable risk score ($R \in [0, 100]$) and severity tier (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`). Missing data is flagged with an explicit uncertainty penalty.
5. **Urgency Prioritization**: The prioritization service scores and ranks active incidents based on depth, blockage severity, and report age.
6. **Agent Recommendation**: The Strands agent calls explicit tools to recommend required machinery (e.g. Super-Sucker Hydro-Vacuum rig, Mobile Dewatering pumps, or Desilting crews).
7. **Human Supervisor Review**: A municipal dispatcher approves or rejects the recommendation in the Human Approval Queue.
8. **Response Task Dispatch**: Approval dispatches a response task (`IN_PROGRESS`). Idempotency guards prevent duplicate dispatch orders. Dispatches explicitly state physical drain clearance is ongoing.
9. **Resolution Update**: Field teams record completed clearance notes and photographic evidence (`RESOLVED`).
10. **Telemetry Verification**: Culvert flow rate ($> 20\text{ LPS}$) and residual depth ($< 5\text{ cm}$) are verified. Successful checks transition to `VERIFIED`; failed checks transition to `NEEDS_HUMAN_REVIEW`.

---

## The 12 Strands Agent Tools

Located in [`backend/app/agent/tools.py`](backend/app/agent/tools.py):
1. `get_rainfall_forecast(latitude, longitude, ward_id)`: Fetches radar intensity and 2-hour forecast.
2. `get_historical_waterlogging(ward_id, location_id)`: Checks ward flood history and hotspot status.
3. `get_nearby_incidents(latitude, longitude, radius_km)`: Identifies active reports within 2 km.
4. `get_drainage_status(ward_id, drain_id)`: Retrieves conduit capacity and structural status.
5. `calculate_waterlogging_risk(incident_id)`: Invokes deterministic mathematical scoring.
6. `prioritize_incident(incident_id)`: Evaluates urgency score and queue ranking.
7. `recommend_response(incident_id)`: Generates equipment and task plan.
8. `request_human_approval(incident_id, reason)`: Queues plan for supervisor review.
9. `create_response_task(incident_id, action_type, assigned_unit, priority)`: Dispatches task (idempotent).
10. `record_resolution(incident_id, resolution_notes, evidence_url)`: Logs field clearance.
11. `verify_resolution(incident_id, sensor_flow_rate_lps, post_clearance_depth_cm)`: Verifies telemetry.
12. `get_incident_status(incident_id)`: Reads complete lifecycle state and audit records.

---

## Quickstart & Local Setup

### 1. Backend Setup & Test Execution

```bash
# Clone and enter workspace
cd monsoon-sentinel

# Run automated test suite
python -m pytest -v
```

All 13 deterministic tests will run:
- `test_risk_engine.py`: Normalization formulas, weights, missing data uncertainty penalty.
- `test_prioritization.py`: Urgency score, multi-incident rank ordering.
- `test_lifecycle.py`: State transitions, rejection branch, invalid transition guards.
- `test_idempotency.py`: Prevention of duplicate response task dispatches.
- `test_verification.py`: Telemetry verification (`VERIFIED` vs `NEEDS_HUMAN_REVIEW`).
- `test_api_workflow.py`: Complete 10-step end-to-end API integration test.

### 2. Start the Backend Server

```bash
cd backend
python -m uvicorn app.api.main:app --port 8000 --reload
```
- API Documentation (Swagger UI): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/`

### 3. Start the Frontend Dashboard

In a second terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## Seed Data & Inspection

The local MVP automatically pre-seeds the SQLite database on startup with 4 realistic municipal incidents across urban wards:
1. **INC-1 (Ward 12 - Central Metro)**: Complete drain blockage near metro underpass; pre-loaded in `AWAITING_APPROVAL`.
2. **INC-2 (Ward 07 - South Lakeside Basin)**: Severe culvert overflow near hospital corridor; pre-approved by supervisor and `IN_PROGRESS`.
3. **INC-3 (Ward 04 - North Industrial Estate)**: Partial silt blockage; in `ANALYZING`.
4. **INC-4 (Ward 19 - Eastern Hills Heights)**: Clear drain with downhill cloudburst runoff; brand `NEW`.

---

## Architectural Guardrails

- **Zero Cloud Costs / No Hardcoded AWS Credentials**: Runs completely offline using `SageMakerInferenceAdapter` mock mode.
- **Repository Abstraction**: All storage interactions use `IncidentRepositoryBase`, facilitating seamless transition to AWS DynamoDB in Phase 2.
- **Derived Dashboard Metrics**: All statistics (counts, severities, average depth) are dynamically computed from application state; never hardcoded.
- **Human In The Loop**: Physical response tasks cannot be executed without supervisor authorization.
