"""
Token models for email verification and password reset
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import secrets

from app.core.database import Base


class VerificationToken(Base):
    """Email verification token"""

    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="verification_tokens")

    @classmethod
    def generate_token(cls):
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    @classmethod
    def create_for_user(cls, user_id: int, hours_valid: int = 24):
        """Create a new verification token for a user"""
        token = cls.generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=hours_valid)

        return cls(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )

    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return not self.used and self.expires_at > datetime.now(timezone.utc)


class PasswordResetToken(Base):
    """Password reset token"""

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="password_reset_tokens")

    @classmethod
    def generate_token(cls):
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    @classmethod
    def create_for_user(cls, user_id: int, hours_valid: int = 1):
        """Create a new password reset token for a user"""
        token = cls.generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=hours_valid)

        return cls(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )

    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return not self.used and self.expires_at > datetime.now(timezone.utc)
