"""
Authentication API endpoints.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.core.config import settings
from app.models.user import User, UserPreferences
from app.schemas.user import (
    UserCreate,
    UserLogin,
    User as UserSchema,
    Token,
)

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
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
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email.lower())
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
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

    # Create default preferences
    preferences = UserPreferences(user_id=new_user.id)
    db.add(preferences)

    # Create default collections
    from app.models.collection import Collection

    default_collections = [
        Collection(
            user_id=new_user.id,
            name="Favorites",
            description="Your favorite recipes",
            is_default=True,
            icon="⭐"
        ),
    ]

    for collection in default_collections:
        db.add(collection)

    await db.commit()
    await db.refresh(new_user)

    # TODO: Send verification email

    return new_user


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
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


# TODO: Implement these endpoints for full MVP
# @router.post("/forgot-password")
# async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
#     """Send password reset email."""
#     pass


# @router.post("/reset-password")
# async def reset_password(token: str, new_password: str, db: AsyncSession = Depends(get_db)):
#     """Reset password with token."""
#     pass


# @router.post("/verify-email")
# async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
#     """Verify user email with token."""
#     pass


# @router.post("/resend-verification")
# async def resend_verification(email: str, db: AsyncSession = Depends(get_db)):
#     """Resend verification email."""
#     pass
