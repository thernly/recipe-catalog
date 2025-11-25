"""User model."""

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models._utils import utc_now


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for IdP-only accounts
    display_name = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)  # Track when email was verified
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    recipes = relationship("Recipe", back_populates="owner", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="owner", cascade="all, delete-orphan")
    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    verification_tokens = relationship(
        "VerificationToken", back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )
    identity_providers = relationship(
        "IdentityProvider", back_populates="user", cascade="all, delete-orphan"
    )
    household_memberships = relationship(
        "HouseholdMember", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    async def has_valid_auth_method(self, db: AsyncSession) -> bool:
        """
        Check if user has at least one valid authentication method.

        OAuth users (hashed_password is NULL) must have at least one identity provider.
        This prevents orphaned users with no way to authenticate.

        Returns:
            True if user has valid auth method, False otherwise
        """
        # Users with password always have a valid auth method
        if self.hashed_password is not None:
            return True

        # OAuth-only users must have at least one identity provider
        from app.models.identity_provider import IdentityProvider

        result = await db.execute(
            select(IdentityProvider).where(IdentityProvider.user_id == self.id)
        )
        providers = result.scalars().all()

        return len(providers) > 0


class UserPreferences(Base):
    """User preferences model."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    theme = Column(String(50), default="light", nullable=False)
    default_view = Column(String(20), default="grid", nullable=False)
    default_sort = Column(String(50), default="recently_added", nullable=False)
    recipes_per_page = Column(Integer, default=24, nullable=False)
    email_notifications = Column(Boolean, default=False, nullable=False)
    timezone = Column(String(100), default="UTC", nullable=False)
    custom_cuisines = Column(JSON, default=list, nullable=False)
    custom_categories = Column(JSON, default=list, nullable=False)
    dietary_preferences = Column(
        JSON, default=list, nullable=False
    )  # e.g., ["vegetarian", "gluten-free"]
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")
