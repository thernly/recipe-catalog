"""Personal API token model.

Tokens let a client such as the Recipe Siphon browser extension call the intake routes
(`/api/v1/intake/*`) and nothing else. Only a SHA-256 hash of each token is stored; the
plain value is shown once, when it is created. Tokens do not expire and are revoked by
setting `revoked_at`.
"""

import secrets

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.constants import API_TOKEN_BYTES, API_TOKEN_PREFIX
from app.core.database import Base
from app.core.security import hash_token
from app.models._utils import utc_now


class ApiToken(Base):
    """A personal API token, scoped to the intake routes."""

    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    # First characters of the token, shown in the settings list so a user can tell
    # tokens apart without the full value
    token_prefix = Column(String(16), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_tokens")

    __table_args__ = (Index("ix_api_tokens_user_revoked", "user_id", "revoked_at"),)

    @staticmethod
    def generate_token() -> str:
        """Generate a new plain-text token."""
        return API_TOKEN_PREFIX + secrets.token_urlsafe(API_TOKEN_BYTES)

    @classmethod
    def create_for_user(cls, user_id: int, name: str) -> tuple["ApiToken", str]:
        """Create a token row for a user. Returns the row and the plain token."""
        raw_token = cls.generate_token()
        instance = cls(
            user_id=user_id,
            name=name,
            token_hash=hash_token(raw_token),
            token_prefix=raw_token[: len(API_TOKEN_PREFIX) + 6],
        )
        return instance, raw_token
