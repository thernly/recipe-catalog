"""
CSRF protection middleware using double-submit cookie pattern.

This provides defense-in-depth protection against CSRF attacks in addition to
SameSite cookies. The middleware validates that state-changing requests include
a valid CSRF token.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.security import verify_csrf_token


# Paths that don't require CSRF protection (authentication endpoints that set the token)
CSRF_EXEMPT_PATHS = [
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
    "/api/v1/oauth/",  # Prefix match for OAuth endpoints
    "/api/auth/register",  # Legacy path (for tests)
    "/api/auth/login",  # Legacy path (for tests)
    "/api/auth/logout",  # Legacy path (for tests)
    "/health",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
]

# HTTP methods that require CSRF protection (state-changing operations)
CSRF_PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate CSRF tokens on state-changing requests.

    Uses double-submit cookie pattern:
    1. Client receives CSRF token on login/register (in cookie + response body)
    2. Client sends token in X-CSRF-Token header for state-changing requests
    3. Middleware validates cookie token matches header token
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and validate CSRF token if required."""
        # Skip CSRF protection in testing environment
        if settings.ENVIRONMENT == "testing":
            return await call_next(request)

        # Skip CSRF check for safe methods (GET, HEAD, OPTIONS)
        if request.method not in CSRF_PROTECTED_METHODS:
            return await call_next(request)

        # Skip CSRF check for exempt paths
        path = request.url.path
        if any(path.startswith(exempt) for exempt in CSRF_EXEMPT_PATHS):
            return await call_next(request)

        # Get CSRF token from cookie and header
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("x-csrf-token")

        # Validate CSRF token
        if not verify_csrf_token(csrf_cookie, csrf_header):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error_code": "csrf_token_invalid",
                    "message": "CSRF token validation failed. Please refresh and try again.",
                    "details": {},
                },
            )

        # Token valid, continue processing request
        return await call_next(request)
