"""
Recipe Catalog API - Main Application
FastAPI backend for recipe management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Include API routers
from app.api import (
    ai,
    auth,
    collections,
    export,
    households,
    import_recipes,
    meal_plans,
    oauth,
    recipes,
    shopping_lists,
    users,
)
from app.api.v1 import api_v1_router
from app.core.config import settings

# Database and core dependencies
from app.core.database import AsyncSessionLocal, cleanup_expired_data, close_db, init_db
from app.core.exceptions import AppException
from app.core.logging import configure_logging, get_logger
from app.middleware.correlation_id import CorrelationIdMiddleware


# Configure structured logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()

    async with AsyncSessionLocal() as session:
        try:
            deleted_count = await cleanup_expired_data(session)
            if deleted_count > 0:
                logger.info(
                    "startup_cleanup_success", deleted_count=deleted_count
                )
        except Exception as e:
            logger.warning(
                "startup_cleanup_failed", error=str(e)
            )

    yield
    # Shutdown
    await close_db()


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Privacy-focused recipe catalog API. All new endpoints are under /api/v1/. "
                "Legacy /api/* endpoints are deprecated.",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Add GZip compression for responses > 1000 bytes
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add correlation ID middleware for request tracing
app.add_middleware(CorrelationIdMiddleware)


# Deprecation warning middleware for old API routes
@app.middleware("http")
async def add_deprecation_warning(request: Request, call_next):
    """Add deprecation warning to old /api/* routes."""
    response = await call_next(request)

    # Add deprecation header for old API routes (not v1)
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/v1/"):
        response.headers["X-API-Deprecation"] = (
            "This endpoint is deprecated. Please use /api/v1/* endpoints instead."
        )
        response.headers["X-API-Version"] = "legacy"
    elif request.url.path.startswith("/api/v1/"):
        response.headers["X-API-Version"] = "v1"

    return response


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Environment-specific Content Security Policy
    if settings.ENVIRONMENT == "production":
        # Strict CSP for production - no inline scripts
        csp_directives = [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self'",
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
    else:
        # Relaxed CSP for development - allow hot reload and dev tools
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow dev tools
            "style-src 'self' 'unsafe-inline'",  # Allow inline styles for dev
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self' ws: wss:",  # Allow WebSocket for hot reload
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]

    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    return response


# Exception handlers
from fastapi.exceptions import HTTPException


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTPException with consistent error response format.

    Converts FastAPI's default {"detail": "error"} format to our standard
    {"error_code": "...", "message": "...", "details": {}} format.
    """
    # Map HTTP status codes to error codes
    error_code_map = {
        400: "INVALID_INPUT",
        401: "UNAUTHORIZED",
        403: "UNAUTHORIZED",
        404: "RESOURCE_NOT_FOUND",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        503: "EXTERNAL_SERVICE_ERROR",
    }

    error_code = error_code_map.get(exc.status_code, "INTERNAL_ERROR")

    logger.error(
        "http_exception",
        url=str(request.url),
        status_code=exc.status_code,
        detail=str(exc.detail),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": error_code,
            "message": str(exc.detail),
            "details": {},
        },
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    logger.error(
        "application_error",
        url=str(request.url),
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and return consistent error format."""
    logger.error("validation_error", url=str(request.url), errors=exc.errors())

    # Convert Pydantic errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        # Create a serializable copy of the error dict
        error_dict = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": str(error.get("input")) if error.get("input") is not None else None,
        }
        # Add ctx if present, but convert non-serializable values
        if "ctx" in error:
            error_dict["ctx"] = {k: str(v) for k, v in error["ctx"].items()}
        errors.append(error_dict)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": errors},
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other uncaught exceptions with consistent error format."""
    logger.exception("unhandled_exception", url=str(request.url), error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "details": {"error": str(exc)} if settings.DEBUG else {},
        },
    )


# Root endpoint
@app.get("/")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def root(request: Request):
    """Root endpoint - API health check."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - no rate limiting."""
    return {"status": "ok"}


# Include v1 API routes
app.include_router(api_v1_router)

# Include legacy routes for backward compatibility (deprecated)
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication (Legacy)"])
app.include_router(oauth.router, prefix="/api/auth", tags=["OAuth (Legacy)"])
app.include_router(users.router, prefix="/api/users", tags=["Users (Legacy)"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["Recipes (Legacy)"])
app.include_router(collections.router, prefix="/api/collections", tags=["Collections (Legacy)"])
app.include_router(export.router, prefix="/api/export", tags=["Export (Legacy)"])
app.include_router(import_recipes.router, prefix="/api/import", tags=["Import (Legacy)"])
app.include_router(households.router, prefix="/api/households", tags=["Households (Legacy)"])
app.include_router(meal_plans.router, prefix="/api/meal-plans", tags=["Meal Plans (Legacy)"])
app.include_router(shopping_lists.router, prefix="/api/shopping-lists", tags=["Shopping Lists (Legacy)"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI (Legacy)"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
