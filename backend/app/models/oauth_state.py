"""OAuth state storage model for CSRF protection."""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime, timedelta, timezone
import secrets

from app.core.database import Base
from app.models._utils import utc_now


class OAuthState(Base):
    """OAuth state token storage for CSRF protection."""

    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    data = Column(JSON, nullable=False)  # Stores provider and link_user_id
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    @classmethod
    def generate_token(cls):
        """Generate a secure random state token."""
        return secrets.token_urlsafe(32)

    @classmethod
    def create_state(
        cls, provider: str, link_user_id: int = None, minutes_valid: int = 10
    ):
        """Create a new OAuth state token.

        Args:
            provider: OAuth provider name (google, microsoft, github)
            link_user_id: Optional user ID if linking accounts
            minutes_valid: Token validity period in minutes (default: 10)
        """
        token = cls.generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes_valid)
        data = {"provider": provider, "link_user_id": link_user_id}

        return cls(
            token=token,
            data=data,
            expires_at=expires_at,
        )

    def is_valid(self) -> bool:
        """Check if state token is still valid."""
        return self.expires_at > datetime.now(timezone.utc)

    @classmethod
    async def cleanup_expired(cls, db_session):
        """Delete expired OAuth state tokens.

        Args:
            db_session: Database session for cleanup operation
        """
        from sqlalchemy import delete

        now = datetime.now(timezone.utc)
        stmt = delete(cls).where(cls.expires_at < now)
        result = await db_session.execute(stmt)
        await db_session.commit()
        return result.rowcount
