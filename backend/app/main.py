import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db_models
from app.core.security import get_password_hash
from app.core.seed_data import seed_student_demo_data
from app.models.user import User, UserRole
from app.services import azure_storage
from app.services import blob_qa_service

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("uniassist")


async def seed_initial_accounts():
    """
    Seed standard development/demo accounts for Student, Faculty, and Admin
    if they don't already exist.
    """
    if not settings.SEED_DEMO_DATA:
        return

    async with AsyncSessionLocal() as session:
        # Check Admin
        admin_res = await session.execute(
            select(User).where(User.email == settings.ADMIN_DEFAULT_EMAIL.lower())
        )
        if not admin_res.scalar_one_or_none():
            admin_user = User(
                email=settings.ADMIN_DEFAULT_EMAIL.lower(),
                hashed_password=get_password_hash(settings.ADMIN_DEFAULT_PASSWORD),
                full_name="University Administrator",
                role=UserRole.ADMIN,
                university_id="ADM001",
                is_active=True,
                is_verified=True,
            )
            session.add(admin_user)
            logger.info("Default Administrator account seeded (%s)", settings.ADMIN_DEFAULT_EMAIL)

        # Check Student
        stu_res = await session.execute(
            select(User).where(User.email == settings.STUDENT_DEFAULT_EMAIL.lower())
        )
        if not stu_res.scalar_one_or_none():
            student_user = User(
                email=settings.STUDENT_DEFAULT_EMAIL.lower(),
                hashed_password=get_password_hash(settings.STUDENT_DEFAULT_PASSWORD),
                full_name="Alex Student",
                role=UserRole.STUDENT,
                university_id="STU1001",
                is_active=True,
                is_verified=True,
            )
            session.add(student_user)
            logger.info("Default Student account seeded (%s)", settings.STUDENT_DEFAULT_EMAIL)

        # Check Faculty
        fac_res = await session.execute(
            select(User).where(User.email == settings.FACULTY_DEFAULT_EMAIL.lower())
        )
        if not fac_res.scalar_one_or_none():
            faculty_user = User(
                email=settings.FACULTY_DEFAULT_EMAIL.lower(),
                hashed_password=get_password_hash(settings.FACULTY_DEFAULT_PASSWORD),
                full_name="Prof. Sarah Jenkins",
                role=UserRole.FACULTY,
                university_id="FAC2001",
                is_active=True,
                is_verified=True,
            )
            session.add(faculty_user)
            logger.info("Default Faculty account seeded (%s)", settings.FACULTY_DEFAULT_EMAIL)

        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown event management.
    """
    logger.info("Starting up %s (version: %s)...", settings.APP_NAME, settings.APP_VERSION)
    try:
        await init_db_models()
        await seed_initial_accounts()
        await seed_student_demo_data()
        await azure_storage.ensure_containers_exist()
        # Pre-load blob text cache in background (Approach B)
        asyncio.create_task(blob_qa_service.load_all_blobs())
    except Exception as e:
        logger.warning("Database bootstrap notice (PostgreSQL might be initializing or offline): %s", e)
    
    yield
    
    logger.info("Shutting down %s...", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-grade University Student Support AI Agent Platform. "
        "Integrates Microsoft Azure AI Foundry, Azure OpenAI, Azure AI Search (Foundry IQ), "
        "PostgreSQL, and role-based student services."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# CORS Middleware
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# Standardized Error Handlers (Section 27 Specification)
# ------------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Standardized HTTP error response format.
    Never exposes internal tracebacks to the client.
    """
    status_codes_to_code = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "RESOURCE_NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
    }
    error_code = status_codes_to_code.get(exc.status_code, "ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": exc.detail,
            }
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic request body/query parameter validation errors cleanly.
    """
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors.append(f"{loc}: {err.get('msg')}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload.",
                "details": errors,
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all unhandled internal exception handler.
    Logs error securely without exposing internals to the user.
    """
    logger.error("Unhandled Exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact university support if this persists.",
            }
        },
    )


# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
