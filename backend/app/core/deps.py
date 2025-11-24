"""
Dependency functions for FastAPI routes.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.household import Household, HouseholdMember
from app.models.user import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token in cookie or Authorization header.

    Args:
        request: Request object to read cookies/headers
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Get token from Authorization header first (preferred for API clients/tests)
    # then fall back to cookie (for browser-based auth)
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix

    # Fall back to cookie if no Authorization header
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    # Get user ID from token
    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current authenticated and verified user.

    Args:
        current_user: The current authenticated user

    Returns:
        User: The authenticated and verified user

    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    return current_user


async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Get the current user if authenticated, None otherwise.
    Useful for endpoints that work for both authenticated and anonymous users.

    Args:
        request: Request object to read cookies
        db: Database session

    Returns:
        Optional[User]: The authenticated user or None
    """
    # Check if access token cookie exists
    if not request.cookies.get("access_token"):
        return None

    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


async def get_user_household(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Household:
    """
    Get the household that the current user belongs to.

    Args:
        current_user: The authenticated user
        db: Database session

    Returns:
        Household: The user's household

    Raises:
        HTTPException: If user doesn't belong to a household
    """
    result = await db.execute(
        select(Household).join(HouseholdMember).where(HouseholdMember.user_id == current_user.id)
    )
    household = result.scalar_one_or_none()

    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not belong to a household",
        )

    return household
