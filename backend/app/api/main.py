from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.exceptions import (
    IncidentError,
    InvalidStateTransitionError,
    IncidentNotFoundError,
    TaskAlreadyExistsError,
    VerificationFailedError
)
from app.api.routes.incidents import router as incidents_router
from app.api.routes.workflow import router as workflow_router
from app.api.routes.agent import router as agent_router
from app.api.routes.stats import router as stats_router
from app.db.seed import seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize sample seed data if database is fresh
    try:
        seed_database()
    except Exception as e:
        print(f"Seed initialization note: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-assisted urban waterlogging risk and response system for municipal flood management.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware (permitting Vite frontend during local MVP development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Domain Exception Handlers
@app.exception_handler(IncidentNotFoundError)
async def incident_not_found_handler(request: Request, exc: IncidentNotFoundError):
    return JSONResponse(status_code=404, content={"error": "NOT_FOUND", "message": str(exc)})

@app.exception_handler(InvalidStateTransitionError)
async def invalid_transition_handler(request: Request, exc: InvalidStateTransitionError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "INVALID_STATE_TRANSITION",
            "message": str(exc),
            "current_status": exc.current_status,
            "target_status": exc.target_status
        }
    )

@app.exception_handler(TaskAlreadyExistsError)
async def duplicate_task_handler(request: Request, exc: TaskAlreadyExistsError):
    return JSONResponse(
        status_code=409,
        content={"error": "TASK_ALREADY_EXISTS", "message": str(exc), "existing_task_id": exc.existing_task_id}
    )

@app.exception_handler(VerificationFailedError)
async def verification_failed_handler(request: Request, exc: VerificationFailedError):
    return JSONResponse(
        status_code=422,
        content={"error": "VERIFICATION_FAILED", "message": str(exc)}
    )

from app.api.routes.evidence import router as evidence_router

# Include Routers
app.include_router(incidents_router, prefix=settings.API_V1_PREFIX)
app.include_router(workflow_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_router, prefix=settings.API_V1_PREFIX)
app.include_router(stats_router, prefix=settings.API_V1_PREFIX)
app.include_router(evidence_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "status": "OPERATIONAL",
        "mode": "LOCAL_MVP",
        "mock_sagemaker": settings.USE_MOCK_SAGEMAKER,
        "docs_url": "/docs"
    }
