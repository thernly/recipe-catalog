"""
Recipe Catalog API - Main Application
FastAPI backend for recipe management.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import api_v1_router
from app.core.config import settings

# Database and core dependencies
from app.core.database import AsyncSessionLocal, cleanup_expired_data, close_db, init_db
from app.core.exceptions import AppException
from app.core.logging import configure_logging, get_logger
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.csrf import CSRFMiddleware


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
                logger.info("startup_cleanup_success", deleted_count=deleted_count)
        except Exception as e:
            logger.warning("startup_cleanup_failed", error=str(e))

    yield
    # Shutdown
    await close_db()


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Privacy-focused recipe catalog API. All endpoints are under /api/v1/.",
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

# Add CSRF protection middleware (defense-in-depth with SameSite cookies)
app.add_middleware(CSRFMiddleware)


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


# Request size limit middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Limit request body size to prevent memory exhaustion attacks."""
    # Get Content-Length header
    content_length = request.headers.get("content-length")

    if content_length:
        content_length = int(content_length)
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert MB to bytes

        if content_length > max_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error_code": "request_too_large",
                    "message": f"Request body too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB",
                    "details": {},
                },
            )

    return await call_next(request)


# Exception handlers


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTPException with consistent error response format.

    Converts FastAPI's default {"detail": "error"} format to our standard
    {"error_code": "...", "message": "...", "details": {}} format.
    Includes correlation_id for client-side debugging.
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

    # Get correlation ID from structlog context or request headers
    correlation_id = structlog.contextvars.get_contextvars().get(
        "correlation_id"
    ) or request.headers.get("X-Correlation-ID")

    logger.error(
        "http_exception",
        url=str(request.url),
        status_code=exc.status_code,
        detail=str(exc.detail),
    )

    response_content = {
        "error_code": error_code,
        "message": str(exc.detail),
        "details": {},
    }

    # Include correlation_id for debugging if available
    if correlation_id:
        response_content["correlation_id"] = correlation_id

    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions. Includes correlation_id for debugging."""
    # Get correlation ID from structlog context or request headers
    correlation_id = structlog.contextvars.get_contextvars().get(
        "correlation_id"
    ) or request.headers.get("X-Correlation-ID")

    logger.error(
        "application_error",
        url=str(request.url),
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )

    response_content = {
        "error_code": exc.error_code,
        "message": exc.message,
        "details": exc.details,
    }

    # Include correlation_id for debugging if available
    if correlation_id:
        response_content["correlation_id"] = correlation_id

    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and return consistent error format. Includes correlation_id for debugging."""
    # Get correlation ID from structlog context or request headers
    correlation_id = structlog.contextvars.get_contextvars().get(
        "correlation_id"
    ) or request.headers.get("X-Correlation-ID")

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

    response_content = {
        "error_code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "details": {"errors": errors},
    }

    # Include correlation_id for debugging if available
    if correlation_id:
        response_content["correlation_id"] = correlation_id

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response_content,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other uncaught exceptions with consistent error format. Includes correlation_id for debugging."""
    # Get correlation ID from structlog context or request headers
    correlation_id = structlog.contextvars.get_contextvars().get(
        "correlation_id"
    ) or request.headers.get("X-Correlation-ID")

    logger.exception("unhandled_exception", url=str(request.url), error=str(exc))

    response_content = {
        "error_code": "INTERNAL_ERROR",
        "message": "Internal server error",
        "details": {"error": str(exc)} if settings.DEBUG else {},
    }

    # Include correlation_id for debugging if available
    if correlation_id:
        response_content["correlation_id"] = correlation_id

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_content,
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
