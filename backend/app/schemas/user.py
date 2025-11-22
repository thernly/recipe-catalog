"""User-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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
    display_name: str | None = Field(None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
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
    refresh_token: str | None = None  # Optional for backwards compatibility


class TokenData(BaseModel):
    """Data stored in JWT token."""

    user_id: int
    email: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


# ============================================
# User Profile
# ============================================


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    display_name: str | None = None


class User(UserBase):
    """Full user schema (response)."""

    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    display_name: str | None = Field(None, max_length=100)
    email: EmailStr | None = None


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str
    new_password: str = Field(..., min_length=12)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        return validate_password_complexity(v)


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset."""

    token: str
    new_password: str = Field(..., min_length=12)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
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

    theme: str = Field("light", pattern="^(light|dark|high-contrast|system|classic|professional)$")
    default_view: str = Field("grid", pattern="^(grid|list)$")
    default_sort: str = "recently_added"
    recipes_per_page: int = Field(24, ge=12, le=100)
    email_notifications: bool = False
    timezone: str = "UTC"
    custom_cuisines: list[str] = Field(default_factory=list)
    custom_categories: list[str] = Field(default_factory=list)
    dietary_preferences: list[str] = Field(default_factory=list)


class UserPreferences(UserPreferencesBase):
    """User preferences response schema."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""

    theme: str | None = Field(
        None, pattern="^(light|dark|high-contrast|system|classic|professional)$"
    )
    default_view: str | None = Field(None, pattern="^(grid|list)$")
    default_sort: str | None = None
    recipes_per_page: int | None = Field(None, ge=12, le=100)
    email_notifications: bool | None = None
    timezone: str | None = None
    custom_cuisines: list[str] | None = None
    custom_categories: list[str] | None = None
    dietary_preferences: list[str] | None = None
