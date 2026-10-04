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
from app.core.constants import API_TOKEN_PREFIX
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

# Paths where a personal API token may stand in for the CSRF check (see below)
API_TOKEN_PATH_PREFIX = "/api/v1/intake"


def is_api_token_request(request: Request) -> bool:
    """
    True for a request to the intake routes that carries a personal API token.

    CSRF rides on ambient cookies; a token in the Authorization header is not ambient (a
    cross-site page cannot set it without a CORS preflight), so these requests skip the
    check. The token is not validated here: `get_intake_user` does that and, when a
    token is present, never falls back to the session cookie, so a forged or bogus token
    cannot turn into a cookie-authenticated request. Cookie-authenticated requests to the
    same paths are still checked.
    """
    path = request.url.path
    if path != API_TOKEN_PATH_PREFIX and not path.startswith(API_TOKEN_PATH_PREFIX + "/"):
        return False
    auth_header = request.headers.get("authorization", "")
    return auth_header.startswith("Bearer " + API_TOKEN_PREFIX)


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

        # Skip CSRF check for personal-API-token requests to the intake routes
        if is_api_token_request(request):
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
