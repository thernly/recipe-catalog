"""
Authentication API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user import User, UserPreferences
from app.schemas.user import (
    UserCreate,
    UserLogin,
    User as UserSchema,
    Token,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResendVerificationRequest,
)

router = APIRouter()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/hour")
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
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
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
    except Exception as e:
        logger.exception(f"Error during registration for {user_data.email}: {str(e)}")
        raise


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT token.

    Args:
        login_data: Login credentials
        db: Database session

    Returns:
        Token: JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == login_data.email.lower())
    )
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout():
    """
    Logout user (client-side token removal).
    Since we're using JWT, actual logout happens on the client side.

    Returns:
        dict: Success message
    """
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
@limiter.limit("3/hour")
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
    from app.models.token import PasswordResetToken
    from app.core.email import email_service

    # Always return success to prevent email enumeration
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        # Invalidate any existing reset tokens
        existing_tokens_result = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id, PasswordResetToken.used == False
            )
        )
        existing_tokens = existing_tokens_result.scalars().all()
        for token in existing_tokens:
            token.used = True

        # Create new reset token
        reset_token = PasswordResetToken.create_for_user(user.id, hours_valid=1)
        db.add(reset_token)
        await db.commit()

        # Send email
        email_service.send_password_reset_email(
            to_email=user.email, reset_token=reset_token.token, user_name=user.display_name
        )

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
@limiter.limit("5/hour")
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
        raise HTTPException(
            status_code=400, detail="Invalid or expired reset token"
        )

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
    result = await db.execute(
        select(VerificationToken).where(VerificationToken.token == token)
    )
    verification_token = result.scalar_one_or_none()

    if not verification_token or not verification_token.is_valid():
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification token"
        )

    # Get user
    user_result = await db.execute(
        select(User).where(User.id == verification_token.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Mark user as verified
    user.is_verified = True
    verification_token.used = True

    await db.commit()

    return {"message": "Email successfully verified"}


@router.post("/resend-verification")
async def resend_verification(
    request: ResendVerificationRequest, db: AsyncSession = Depends(get_db)
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
    from app.models.token import VerificationToken
    from app.core.email import email_service

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
            VerificationToken.user_id == user.id, VerificationToken.used == False
        )
    )
    existing_tokens = existing_tokens_result.scalars().all()
    for token in existing_tokens:
        token.used = True

    # Create new verification token
    verification_token = VerificationToken.create_for_user(user.id, hours_valid=24)
    db.add(verification_token)
    await db.commit()

    # Send email
    email_service.send_verification_email(
        to_email=user.email,
        verification_token=verification_token.token,
        user_name=user.display_name,
    )

    return {"message": "Verification email sent"}
