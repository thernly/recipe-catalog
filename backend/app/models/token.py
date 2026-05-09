"""
Token models for email verification and password reset
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.security import hash_token
from app.models._utils import utc_now


class VerificationToken(Base):
    """Email verification token"""

    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationship
    user = relationship("User", back_populates="verification_tokens")

    @classmethod
    def generate_token(cls):
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    @classmethod
    def create_for_user(cls, user_id: int, hours_valid: int = 24):
        """Create a new verification token for a user"""
        raw_token = cls.generate_token()
        expires_at = datetime.now(UTC) + timedelta(hours=hours_valid)

        instance = cls(
            user_id=user_id,
            token=hash_token(raw_token),
            expires_at=expires_at,
        )
        instance.raw_token = raw_token
        return instance

    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return not self.used and self.expires_at > datetime.now(UTC)


class PasswordResetToken(Base):
    """Password reset token"""

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationship
    user = relationship("User", back_populates="password_reset_tokens")

    @classmethod
    def generate_token(cls):
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    @classmethod
    def create_for_user(cls, user_id: int, hours_valid: int = 1):
        """Create a new password reset token for a user"""
        raw_token = cls.generate_token()
        expires_at = datetime.now(UTC) + timedelta(hours=hours_valid)

        instance = cls(
            user_id=user_id,
            token=hash_token(raw_token),
            expires_at=expires_at,
        )
        instance.raw_token = raw_token
        return instance

    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return not self.used and self.expires_at > datetime.now(UTC)
