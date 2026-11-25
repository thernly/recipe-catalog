"""
Authentication API endpoints.
"""

import time
from collections import deque
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select, update
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import (
    AUTH_RATE_LIMIT_REGISTRATION,
    AUTH_RATE_LIMIT_TEST_MODE,
)
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    generate_csrf_token,
    generate_refresh_token,
    get_password_hash,
    get_refresh_token_expiry,
    hash_token,
    session_user_agent,
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
_DUMMY_PASSWORD_HASH = get_password_hash("dummy-login-password-never-valid")
logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)


# Per-account login throttle: at most LOGIN_FAILURE_LIMIT failed attempts per email in a
# sliding LOGIN_FAILURE_WINDOW_S window, on top of the per-IP limit. The window slides, so an
# attacker can only keep an account throttled by continuously spending attempts against it,
# and nothing persists: it is never a durable lockout.
# ponytail: in-process dict, so per-worker; move to a shared store if we run >1 worker.
LOGIN_FAILURE_LIMIT = 10
LOGIN_FAILURE_WINDOW_S = 15 * 60
_login_failures: dict[str, deque[float]] = {}
REFRESH_REUSE_GRACE_S = 30


def _recent_failures(email: str) -> deque[float]:
    cutoff = time.monotonic() - LOGIN_FAILURE_WINDOW_S
    failures = _login_failures.get(email, deque())
    while failures and failures[0] < cutoff:
        failures.popleft()
    return failures


def _record_login_failure(email: str) -> None:
    if len(_login_failures) > 10_000:  # bound memory under email-spraying
        _login_failures.clear()
    failures = _recent_failures(email)
    failures.append(time.monotonic())
    _login_failures[email] = failures


def _get_rate_limit(limit: str) -> str:
    """Return rate limit string or very high limit if testing."""
    if settings.TESTING:
        return AUTH_RATE_LIMIT_TEST_MODE
    return limit


@router.post(
    "/register",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User successfully created"},
        400: {
            "description": "Email already registered or validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "invalid_input",
                        "message": "Email already registered",
                        "details": {},
                    }
                }
            },
        },
        422: {
            "description": "Invalid request format or password requirements not met",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "validation_error",
                        "message": "Validation error",
                        "details": {
                            "errors": [
                                {
                                    "field": "password",
                                    "message": "Password must contain at least one uppercase letter",
                                }
                            ]
                        },
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded (10 requests per minute per IP)",
            "content": {"application/json": {"example": {"error": "Rate limit exceeded"}}},
        },
    },
)
@limiter.limit(lambda: _get_rate_limit(AUTH_RATE_LIMIT_REGISTRATION))
async def register(
    request: Request, response: Response, user_data: UserCreate, db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.

    Creates a new user account with the provided email and password. The password must be at least
    12 characters long and contain at least one uppercase letter, one lowercase letter, and one digit.

    **Rate Limit:** 10 requests per minute per IP address

    **Authentication:** None required

    Args:
        user_data: User registration data (email, password, optional display_name)
        db: Database session

    Returns:
        User: The created user object

    Raises:
        HTTPException 400: If email already exists
        HTTPException 422: If password doesn't meet requirements
        HTTPException 429: If rate limit exceeded
    """
    logger.info("registration_attempt", email=user_data.email)

    try:
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == user_data.email.lower()))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning("registration_failed_duplicate_email", email=user_data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user
        logger.debug("creating_new_user", email=user_data.email)
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
        logger.info("user_created", user_id=new_user.id)

        # Create default preferences
        preferences = UserPreferences(user_id=new_user.id)
        db.add(preferences)

        # Create default household
        from app.services.household import create_default_household_for_new_user

        household = await create_default_household_for_new_user(db, new_user)
        logger.info("user_setup_completed", household_id=household.id, user_id=new_user.id)

        # Create default collections
        from app.models.collection import Collection

        logger.debug("creating_default_collections", user_id=new_user.id)
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

        logger.info("user_registered_successfully", email=new_user.email, user_id=new_user.id)

        # Create tokens and set cookies (same as login)
        access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})

        # Generate and store refresh token
        refresh_token_value = generate_refresh_token()
        refresh_token = RefreshToken(
            token=hash_token(refresh_token_value),
            user_id=new_user.id,
            expires_at=get_refresh_token_expiry(),
            revoked=False,
            user_agent=session_user_agent(request),
        )
        db.add(refresh_token)
        await db.commit()

        # Set httpOnly cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="strict",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token_value,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="strict",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        # Generate and set CSRF token
        csrf_token = generate_csrf_token()
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,
            secure=settings.cookie_secure,
            samesite="strict",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        return new_user
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception:
        # Log unexpected errors and re-raise
        logger.exception("registration_unexpected_error", email=user_data.email)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration. Please try again.",
        )


@router.post(
    "/login",
    responses={
        200: {
            "description": "Login successful - authentication cookies set",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Login successful",
                        "user": {"id": 1, "email": "user@example.com"},
                    }
                }
            },
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "authentication_failed",
                        "message": "Invalid email or password",
                        "details": {},
                    }
                }
            },
        },
        403: {"description": "Account is inactive"},
        429: {
            "description": "Rate limit exceeded (10 requests per minute per IP, "
            "or 10 failed attempts per 15 minutes per account)",
            "content": {"application/json": {"example": {"error": "Rate limit exceeded"}}},
        },
    },
)
@limiter.limit(lambda: _get_rate_limit("10/minute"))
async def login(
    request: Request,
    response: Response,
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and set httpOnly cookies.

    Authenticates the user with email and password. On success, sets secure httpOnly cookies
    for access token and refresh token.

    **Rate Limit:** 10 requests per minute per IP address, plus 10 failed attempts per
    15-minute sliding window per email (429; no persistent lockout)

    **Authentication:** None required

    Args:
        login_data: Login credentials (email and password)
        response: Response object to set cookies
        db: Database session

    Returns:
        dict: Success message with user information

    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 403: If the account is inactive
        HTTPException 429: If the IP or per-account rate limit is exceeded
    """
    request.session.clear()
    email = login_data.email.lower()
    if len(_recent_failures(email)) >= LOGIN_FAILURE_LIMIT:
        logger.warning("login_throttled", email=email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
        )
    # Get user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    password_valid = verify_password(
        login_data.password,
        user.hashed_password if user and user.hashed_password else _DUMMY_PASSWORD_HASH,
    )
    if not user or not user.hashed_password or not password_valid:
        _record_login_failure(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    _login_failures.pop(email, None)
    csrf_token = await issue_session(db, user, request, response)
    return {"message": "Login successful", "csrf_token": csrf_token}


async def issue_session(db: AsyncSession, user: User, request: Request, response: Response) -> str:
    """Store a new refresh token and set access/refresh/CSRF cookies. Returns the CSRF token."""
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    refresh_token_value = generate_refresh_token()
    db.add(
        RefreshToken(
            token=hash_token(refresh_token_value),
            user_id=user.id,
            expires_at=get_refresh_token_expiry(),
            revoked=False,
            user_agent=session_user_agent(request),
        )
    )
    await db.commit()

    # Set httpOnly cookies
    # Access token cookie (15 minutes)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    # Refresh token cookie (7 days)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_value,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    # Generate and set CSRF token (double-submit cookie pattern)
    csrf_token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Frontend needs to read this
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Same as refresh token
    )
    return csrf_token


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
    hashed_refresh_token_value = hash_token(refresh_token_value)
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token == hashed_refresh_token_value)
        .with_for_update()
    )
    refresh_token_record = result.scalar_one_or_none()

    # Validate refresh token exists
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if token is revoked. A token rotated moments ago is almost always a concurrent
    # tab or retry losing the race, so just reject it; reuse after the grace window is
    # treated as theft and revokes every session for the user.
    if refresh_token_record.revoked:
        revoked_at = refresh_token_record.revoked_at
        if revoked_at is not None and not is_expired(
            revoked_at + timedelta(seconds=REFRESH_REUSE_GRACE_S)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
        logger.warning("refresh_token_reuse_detected", user_id=refresh_token_record.user_id)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == refresh_token_record.user_id)
            .values(revoked=True, revoked_at=datetime.now(UTC))
        )
        await db.commit()
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

    # Claim rotation atomically, including on SQLite where FOR UPDATE is ignored.
    claimed: Result[Any] = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.id == refresh_token_record.id, RefreshToken.revoked.is_(False))
        .values(revoked=True, revoked_at=datetime.now(UTC))
        .returning(RefreshToken.id)
    )
    if claimed.scalar_one_or_none() is None:
        await db.rollback()
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    # Generate new refresh token (token rotation for security)
    new_refresh_token_value = generate_refresh_token()
    new_refresh_token = RefreshToken(
        token=hash_token(new_refresh_token_value),
        user_id=user.id,
        expires_at=get_refresh_token_expiry(),
        revoked=False,
        user_agent=refresh_token_record.user_agent,
    )

    # Add and commit new refresh token
    db.add(new_refresh_token)
    await db.commit()

    # Set new httpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token_value,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    # Regenerate CSRF token on refresh for added security
    csrf_token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {"message": "Token refreshed successfully", "csrf_token": csrf_token}


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

    request.session.clear()
    # Get refresh token from cookie
    refresh_token_value = request.cookies.get("refresh_token")

    if refresh_token_value:
        # Revoke the refresh token
        hashed_refresh_token_value = hash_token(refresh_token_value)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == hashed_refresh_token_value)
        )
        refresh_token_record = result.scalar_one_or_none()

        if refresh_token_record and not refresh_token_record.revoked:
            refresh_token_record.revoked = True
            refresh_token_record.revoked_at = datetime.now(UTC)
            await db.commit()

    # Clear cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    response.delete_cookie(key="csrf_token")

    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
@limiter.limit(lambda: _get_rate_limit("3/hour"))
async def forgot_password(
    request: Request, request_data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
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
    result = await db.execute(select(User).where(User.email == request_data.email.lower()))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        # Invalidate any existing reset tokens
        existing_tokens_result = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id, PasswordResetToken.used.is_(False)
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
            reset_token=reset_token.raw_token,
            user_name=user.display_name,
        )

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
@limiter.limit(lambda: _get_rate_limit("5/hour"))
async def reset_password(
    request: Request, request_data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
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
    hashed_request_token = hash_token(request_data.token)
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == hashed_request_token)
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
    user.hashed_password = get_password_hash(request_data.new_password)
    reset_token.used = True
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .values(revoked=True, revoked_at=datetime.now(UTC))
    )

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
    hashed_token = hash_token(token)
    result = await db.execute(
        select(VerificationToken).where(VerificationToken.token == hashed_token)
    )
    verification_token = result.scalar_one_or_none()

    if not verification_token or not verification_token.is_valid():
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    # Get user
    user_result = await db.execute(select(User).where(User.id == verification_token.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if verification_token.pending_email:
        existing = (
            await db.execute(
                select(User).where(
                    User.email == verification_token.pending_email, User.id != user.id
                )
            )
        ).scalar_one_or_none()
        if existing:
            from app.core.exceptions import InvalidInputError

            raise InvalidInputError("Email address is unavailable")
        user.email = verification_token.pending_email
    # Mark user as verified
    user.is_verified = True
    verification_token.used = True

    await db.commit()

    return {"message": "Email successfully verified"}


@router.post("/resend-verification")
@limiter.limit(lambda: _get_rate_limit("3/hour"))
async def resend_verification(
    request: Request, request_data: ResendVerificationRequest, db: AsyncSession = Depends(get_db)
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
    result = await db.execute(select(User).where(User.email == request_data.email.lower()))
    user = result.scalar_one_or_none()

    if not user or user.is_verified or not user.is_active:
        return {"message": "If eligible, a verification email has been sent"}

    # Invalidate existing verification tokens
    existing_tokens_result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.user_id == user.id, VerificationToken.used.is_(False)
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
        verification_token=verification_token.raw_token,
        user_name=user.display_name,
    )

    return {"message": "If eligible, a verification email has been sent"}
