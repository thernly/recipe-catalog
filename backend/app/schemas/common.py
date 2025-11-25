"""Common schemas used across the API."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error details")

    model_config = {"json_schema_extra": {"example": {"error_code": "not_found", "message": "Resource not found", "details": {}}}}


class RateLimitInfo(BaseModel):
    """Information about API rate limits."""

    limit: str = Field(..., description="Rate limit (e.g., '5/minute', '20/hour')")
    scope: str = Field(..., description="What the rate limit applies to (e.g., 'per IP', 'per user')")
    description: str = Field(..., description="Description of what happens when limit is exceeded")

    model_config = {
        "json_schema_extra": {
            "example": {
                "limit": "5/minute",
                "scope": "per IP address",
                "description": "Returns 429 Too Many Requests when exceeded",
            }
        }
    }
