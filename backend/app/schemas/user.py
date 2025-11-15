"""User-related Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


# ============================================
# Shared Validators
# ============================================


def validate_password_complexity(password: str) -> str:
    """
    Shared password validation logic for complexity requirements.

    Args:
        password: The password to validate

    Returns:
        The validated password

    Raises:
        ValueError: If password doesn't meet complexity requirements
    """
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one digit")
    return password


# ============================================
# User Registration & Authentication
# ============================================


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=12)
    display_name: Optional[str] = Field(None, max_length=100)

    @validator("password")
    def validate_password(cls, v):
        """Validate password complexity."""
        return validate_password_complexity(v)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Data stored in JWT token."""

    user_id: int
    email: str


# ============================================
# User Profile
# ============================================


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    display_name: Optional[str] = None


class User(UserBase):
    """Full user schema (response)."""

    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    display_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str
    new_password: str = Field(..., min_length=12)

    @validator("new_password")
    def validate_password(cls, v):
        """Validate password complexity."""
        return validate_password_complexity(v)


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset."""

    token: str
    new_password: str = Field(..., min_length=12)

    @validator("new_password")
    def validate_password(cls, v):
        """Validate password complexity."""
        return validate_password_complexity(v)


class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email."""

    email: EmailStr


# ============================================
# User Preferences
# ============================================


class UserPreferencesBase(BaseModel):
    """Base user preferences schema."""

    theme: str = Field("classic", pattern="^(classic|professional)$")
    default_view: str = Field("grid", pattern="^(grid|list)$")
    default_sort: str = "recently_added"
    recipes_per_page: int = Field(24, ge=12, le=100)
    email_notifications: bool = False
    timezone: str = "UTC"


class UserPreferences(UserPreferencesBase):
    """User preferences response schema."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""

    theme: Optional[str] = Field(None, pattern="^(classic|professional)$")
    default_view: Optional[str] = Field(None, pattern="^(grid|list)$")
    default_sort: Optional[str] = None
    recipes_per_page: Optional[int] = Field(None, ge=12, le=100)
    email_notifications: Optional[bool] = None
    timezone: Optional[str] = None
