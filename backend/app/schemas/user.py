"""User-related Pydantic schemas."""

from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.constants import DEFAULT_CATEGORIES, DEFAULT_CUISINES


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
    password: str = Field(..., min_length=12, max_length=128)
    display_name: str | None = Field(None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        return validate_password_complexity(v)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    # No 128 cap on login: users who registered before the cap must still sign in.
    # 4096 is just a sanity bound; the request-size guard limits bodies anyway.
    password: str = Field(..., max_length=4096)


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
    current_password: str | None = Field(None, max_length=4096)


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str = Field(..., max_length=4096)
    new_password: str = Field(..., min_length=12, max_length=128)

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
    new_password: str = Field(..., min_length=12, max_length=128)

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


Preference = Annotated[str, Field(max_length=100)]


def safe_zone(name: str | None) -> ZoneInfo:
    """ZoneInfo for a stored timezone; legacy free-text values ("PST", "") fall back to UTC."""
    try:
        return ZoneInfo(name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def validate_timezone(value: str | None) -> str | None:
    """Input-only check. An empty string means "unset" and is stored as UTC."""
    if value is not None:
        if not value.strip():
            return "UTC"
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Unknown timezone")
    return value


def coerce_timezone(value: str | None) -> str:
    """Output-side: never fail a read on a legacy invalid value."""
    return safe_zone(value).key


# Every theme name the frontend may save: its `[data-theme]` blocks in app.css, plus
# "system". A new theme must be added here or saving it is rejected with a 422.
THEME_PATTERN = (
    "^(light|dark|high-contrast|system|classic|professional|garden-fresh|bistro"
    "|ember|coastal|farmhouse)$"
)


class UserPreferencesBase(BaseModel):
    """Base user preferences schema."""

    theme: str = Field("light", pattern=THEME_PATTERN)
    default_view: str = Field("grid", pattern="^(grid|list)$")
    default_sort: str = "recently_added"
    recipes_per_page: int = Field(24, ge=12, le=100)
    email_notifications: bool = False
    timezone: str = Field("UTC", max_length=100)
    _timezone = field_validator("timezone", mode="before")(coerce_timezone)
    custom_cuisines: list[Preference] = Field(default_factory=list, max_length=100)
    custom_categories: list[Preference] = Field(default_factory=list, max_length=100)
    dietary_preferences: list[Preference] = Field(default_factory=list, max_length=100)


class UserPreferences(UserPreferencesBase):
    """User preferences response schema."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    # Read-only: the built-in filter options, so the frontend doesn't keep its own copy.
    default_cuisines: list[str] = Field(default_factory=lambda: list(DEFAULT_CUISINES))
    default_categories: list[str] = Field(default_factory=lambda: list(DEFAULT_CATEGORIES))

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""

    theme: str | None = Field(None, pattern=THEME_PATTERN)
    default_view: str | None = Field(None, pattern="^(grid|list)$")
    default_sort: str | None = None
    recipes_per_page: int | None = Field(None, ge=12, le=100)
    email_notifications: bool | None = None
    timezone: str | None = Field(None, max_length=100)
    _timezone = field_validator("timezone")(validate_timezone)
    custom_cuisines: list[Preference] | None = Field(None, max_length=100)
    custom_categories: list[Preference] | None = Field(None, max_length=100)
    dietary_preferences: list[Preference] | None = Field(None, max_length=100)
