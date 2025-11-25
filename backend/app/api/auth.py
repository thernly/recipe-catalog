"""
Authentication API endpoints.
"""

import logging
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import AUTH_RATE_LIMIT_REGISTRATION, AUTH_RATE_LIMIT_TEST_MODE
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    get_password_hash,
    get_refresh_token_expiry,
    verify_password,
)
from app.models._utils import is_expired
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserPreferences
from app.schemas.user import (
    ForgotPasswordRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    UserCreate,
    UserLogin,
)
from app.schemas.user import (
    User as UserSchema,
)


router = APIRouter()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


def _get_rate_limit(limit: str) -> str:
    """Return rate limit string or very high limit if testing."""
    if settings.TESTING:
        return AUTH_RATE_LIMIT_TEST_MODE
    return limit


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: _get_rate_limit(AUTH_RATE_LIMIT_REGISTRATION))
async def register(request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        User: The created user

    Raises:
        HTTPException: If email already exists
    """
    logger.info(f"Registration attempt for email: {user_data.email}")

    try:
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == user_data.email.lower()))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning(f"Registration failed - email already exists: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user
        logger.debug(f"Creating new user: {user_data.email}")
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email.lower(),
            hashed_password=hashed_password,
            display_name=user_data.display_name,
            is_active=True,
            is_verified=False,  # Set to True for MVP (no email verification yet)
        )

        db.add(new_user)
        await db.flush()  # Get the user ID
        logger.debug(f"User created with ID: {new_user.id}")

        # Create default preferences
        logger.debug(f"Creating default preferences for user {new_user.id}")
        preferences = UserPreferences(user_id=new_user.id)
        db.add(preferences)

        # Create default household
        from app.services.household import create_default_household_for_new_user

        logger.debug(f"Creating default household for user {new_user.id}")
        household = await create_default_household_for_new_user(db, new_user)
        logger.debug(
            f"Created household '{household.name}' (ID: {household.id}) for user {new_user.id}"
        )

        # Create default collections
        from app.models.collection import Collection

        logger.debug(f"Creating default collections for user {new_user.id}")
        default_collections = [
            Collection(
                user_id=new_user.id,
                name="Favorites",
                description="Your favorite recipes",
                is_default=True,
                icon="⭐",
            ),
        ]

        for collection in default_collections:
            db.add(collection)

        await db.commit()
        await db.refresh(new_user)

        logger.info(f"User registered successfully: {new_user.email} (ID: {new_user.id})")

        # TODO: Send verification email

        return new_user
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception:
        # Log unexpected errors and re-raise
        logger.exception(f"Unexpected error during registration for {user_data.email}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration. Please try again.",
        )


@router.post("/login")
@limiter.limit(lambda: _get_rate_limit("10/minute"))
async def login(
    request: Request,
    response: Response,
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and set httpOnly cookies.

    Args:
        login_data: Login credentials
        response: Response object to set cookies
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user by email
    result = await db.execute(select(User).where(User.email == login_data.email.lower()))
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # Generate and store refresh token
    refresh_token_value = generate_refresh_token()
    refresh_token = RefreshToken(
        token=refresh_token_value,
        user_id=user.id,
        expires_at=get_refresh_token_expiry(),
        revoked=False,
    )
    db.add(refresh_token)
    await db.commit()

    # Set httpOnly cookies
    # Access token cookie (15 minutes)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.TESTING,  # HTTPS only in production
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    # Refresh token cookie (7 days)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_value,
        httponly=True,
        secure=not settings.TESTING,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {"message": "Login successful"}


@router.post("/refresh")
@limiter.limit(lambda: _get_rate_limit("5/minute"))
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a refresh token for a new access token.

    Args:
        request: Request object to read cookies
        response: Response object to set new cookies
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If refresh token is invalid, expired, or revoked
    """
    from datetime import datetime

    # Get refresh token from cookie
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found",
        )

    # Look up the refresh token with row-level lock to prevent race conditions
    # The with_for_update() ensures that concurrent refresh requests will be serialized
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token == refresh_token_value)
        .with_for_update()
    )
    refresh_token_record = result.scalar_one_or_none()

    # Validate refresh token exists
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if token is revoked
    if refresh_token_record.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Check if token is expired
    if is_expired(refresh_token_record.expires_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Get the user
    user = await db.get(User, refresh_token_record.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create new access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # Generate new refresh token (token rotation for security)
    new_refresh_token_value = generate_refresh_token()
    new_refresh_token = RefreshToken(
        token=new_refresh_token_value,
        user_id=user.id,
        expires_at=get_refresh_token_expiry(),
        revoked=False,
    )

    # Revoke old refresh token
    refresh_token_record.revoked = True
    refresh_token_record.revoked_at = datetime.now(UTC)

    # Add new refresh token
    db.add(new_refresh_token)
    await db.commit()

    # Set new httpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.TESTING,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token_value,
        httponly=True,
        secure=not settings.TESTING,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {"message": "Token refreshed successfully"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user and revoke refresh token.

    Args:
        request: Request object to read cookies
        response: Response object to clear cookies
        db: Database session

    Returns:
        dict: Success message
    """
    from datetime import datetime

    # Get refresh token from cookie
    refresh_token_value = request.cookies.get("refresh_token")

    if refresh_token_value:
        # Revoke the refresh token
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token_value)
        )
        refresh_token_record = result.scalar_one_or_none()

        if refresh_token_record and not refresh_token_record.revoked:
            refresh_token_record.revoked = True
            refresh_token_record.revoked_at = datetime.now(UTC)
            await db.commit()

    # Clear cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
@limiter.limit(lambda: _get_rate_limit("3/hour"))
async def forgot_password(
    req: Request, request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """
    Send password reset email.

    Args:
        request: Email address for password reset
        db: Database session

    Returns:
        dict: Success message (always returns success to prevent email enumeration)
    """
    from sqlalchemy import select

    from app.core.email import email_service
    from app.models.token import PasswordResetToken

    # Always return success to prevent email enumeration
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        # Invalidate any existing reset tokens
        existing_tokens_result = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id, not PasswordResetToken.used
            )
        )
        existing_tokens = existing_tokens_result.scalars().all()
        for token in existing_tokens:
            token.used = True

        # Create new reset token
        reset_token = PasswordResetToken.create_for_user(user.id, hours_valid=1)
        db.add(reset_token)
        await db.commit()

        # Send email asynchronously
        await email_service.send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token.token,
            user_name=user.display_name,
        )

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
@limiter.limit(lambda: _get_rate_limit("5/hour"))
async def reset_password(
    req: Request, request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """
    Reset password with token.

    Args:
        request: Reset token and new password
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If token is invalid or expired
    """
    from sqlalchemy import select

    from app.models.token import PasswordResetToken

    # Find token
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == request.token)
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token or not reset_token.is_valid():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Get user
    user_result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    reset_token.used = True

    await db.commit()

    return {"message": "Password successfully reset"}


@router.post("/verify-email/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verify user email with token.

    Args:
        token: Verification token from email
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If token is invalid or expired
    """
    from sqlalchemy import select

    from app.models.token import VerificationToken

    # Find token
    result = await db.execute(select(VerificationToken).where(VerificationToken.token == token))
    verification_token = result.scalar_one_or_none()

    if not verification_token or not verification_token.is_valid():
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    # Get user
    user_result = await db.execute(select(User).where(User.id == verification_token.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Mark user as verified
    user.is_verified = True
    verification_token.used = True

    await db.commit()

    return {"message": "Email successfully verified"}


@router.post("/resend-verification")
@limiter.limit(lambda: _get_rate_limit("3/hour"))
async def resend_verification(
    req: Request, request: ResendVerificationRequest, db: AsyncSession = Depends(get_db)
):
    """
    Resend verification email.

    Args:
        request: Email address to resend verification
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If user not found or already verified
    """
    from sqlalchemy import select

    from app.core.email import email_service
    from app.models.token import VerificationToken

    # Find user
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    # Invalidate existing verification tokens
    existing_tokens_result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.user_id == user.id, not VerificationToken.used
        )
    )
    existing_tokens = existing_tokens_result.scalars().all()
    for token in existing_tokens:
        token.used = True

    # Create new verification token
    verification_token = VerificationToken.create_for_user(user.id, hours_valid=24)
    db.add(verification_token)
    await db.commit()

    # Send email asynchronously
    await email_service.send_verification_email(
        to_email=user.email,
        verification_token=verification_token.token,
        user_name=user.display_name,
    )

    return {"message": "Verification email sent"}
