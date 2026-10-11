from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from app.api.routes.agent import router as agent_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.stats import router as stats_router
from app.api.routes.workflow import router as workflow_router
from app.core.config import settings
from app.core.exceptions import (
    IncidentError,
    IncidentNotFoundError,
    InvalidStateTransitionError,
    TaskAlreadyExistsError,
    VerificationFailedError,
    SageMakerConfigurationError,
    SageMakerInvocationError,
)
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
    root_path=settings.ROOT_PATH,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware (permitting Vite frontend during local MVP development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
handler = Mangum(app, lifespan="off")


# Domain Exception Handlers
@app.exception_handler(IncidentNotFoundError)
async def incident_not_found_handler(request: Request, exc: IncidentNotFoundError):
    return JSONResponse(
        status_code=404, content={"error": "NOT_FOUND", "message": str(exc)}
    )


@app.exception_handler(InvalidStateTransitionError)
async def invalid_transition_handler(
    request: Request, exc: InvalidStateTransitionError
):
    return JSONResponse(
        status_code=400,
        content={
            "error": "INVALID_STATE_TRANSITION",
            "message": str(exc),
            "current_status": exc.current_status,
            "target_status": exc.target_status,
        },
    )


@app.exception_handler(TaskAlreadyExistsError)
async def duplicate_task_handler(request: Request, exc: TaskAlreadyExistsError):
    return JSONResponse(
        status_code=409,
        content={
            "error": "TASK_ALREADY_EXISTS",
            "message": str(exc),
            "existing_task_id": exc.existing_task_id,
        },
    )


@app.exception_handler(VerificationFailedError)
async def verification_failed_handler(request: Request, exc: VerificationFailedError):
    return JSONResponse(
        status_code=422, content={"error": "VERIFICATION_FAILED", "message": str(exc)}
    )


@app.exception_handler(SageMakerConfigurationError)
async def sagemaker_config_error_handler(request: Request, exc: SageMakerConfigurationError):
    return JSONResponse(
        status_code=503,
        content={"error": "SAGEMAKER_CONFIGURATION_ERROR", "message": str(exc)},
    )


@app.exception_handler(SageMakerInvocationError)
async def sagemaker_invocation_error_handler(request: Request, exc: SageMakerInvocationError):
    return JSONResponse(
        status_code=502,
        content={
            "error": "SAGEMAKER_INVOCATION_ERROR",
            "message": str(exc),
            "endpoint": exc.endpoint_name,
        },
    )


from app.api.routes.evidence import router as evidence_router

# Include Routers
app.include_router(incidents_router, prefix=settings.API_V1_PREFIX)
app.include_router(workflow_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_router, prefix=settings.API_V1_PREFIX)
app.include_router(stats_router, prefix=settings.API_V1_PREFIX)
app.include_router(evidence_router, prefix=settings.API_V1_PREFIX)


from app.core.exceptions import (
    IncidentError,
    IncidentNotFoundError,
    InvalidStateTransitionError,
    TaskAlreadyExistsError,
    VerificationFailedError,
    SageMakerConfigurationError,
    SageMakerInvocationError,
)

@app.exception_handler(SageMakerConfigurationError)
async def sagemaker_config_handler(request: Request, exc: SageMakerConfigurationError):
    return JSONResponse(
        status_code=500,
        content={"error": "SAGEMAKER_CONFIG_ERROR", "message": str(exc)}
    )

@app.exception_handler(SageMakerInvocationError)
async def sagemaker_invocation_handler(request: Request, exc: SageMakerInvocationError):
    return JSONResponse(
        status_code=502,
        content={"error": "SAGEMAKER_INVOCATION_ERROR", "message": str(exc), "endpoint": exc.endpoint_name}
    )

@app.get("/")
def root():
    stage_prefix = settings.ROOT_PATH.rstrip("/")
    return {
        "system": settings.PROJECT_NAME,
        "status": "OPERATIONAL",
        "environment": settings.ENVIRONMENT,
        "storage_backend": settings.STORAGE_BACKEND,
        "dynamodb_table": settings.DYNAMODB_TABLE_NAME,
        "s3_bucket": settings.S3_BUCKET_NAME,
        "inference_mode": "mock" if settings.USE_MOCK_SAGEMAKER else "sagemaker_endpoint",
        "docs_url": f"{stage_prefix}/docs" if stage_prefix else "/docs",
        "openapi_url": f"{stage_prefix}/openapi.json" if stage_prefix else "/openapi.json",
    }
