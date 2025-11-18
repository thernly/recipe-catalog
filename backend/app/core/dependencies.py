"""
FastAPI dependencies for request validation and authentication.
"""

from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.security import validate_csrf_token


async def validate_csrf(
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
) -> str:
    """
    Validate CSRF token from request header.

    This dependency can be added to state-changing endpoints (POST, PUT, DELETE)
    to validate CSRF tokens. It's optional for this JWT-based API but provides
    defense-in-depth.

    Args:
        x_csrf_token: CSRF token from X-CSRF-Token header

    Returns:
        The validated CSRF token

    Raises:
        HTTPException: If CSRF token is missing or invalid
    """
    if not x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token is missing",
        )

    if not validate_csrf_token(x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

    return x_csrf_token
