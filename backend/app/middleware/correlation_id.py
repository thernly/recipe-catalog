"""
Correlation ID middleware for request tracing.

Adds a unique correlation ID to each request for distributed tracing and log correlation.
"""

from uuid import uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to requests.

    The correlation ID is:
    1. Taken from X-Correlation-ID header if present
    2. Generated as a new UUID if not present
    3. Added to structlog context for automatic inclusion in all logs
    4. Added to response headers for client tracking
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and add correlation ID."""
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())

        # Add to structlog context so all logs in this request include it
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response
