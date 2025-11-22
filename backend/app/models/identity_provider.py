"""Identity Provider model for OAuth/OIDC authentication."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models._utils import utc_now


class IdentityProvider(Base):
    """Links external identity providers (Google, Microsoft, etc.) to user accounts."""

    __tablename__ = "identity_providers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_name = Column(String(50), nullable=False)  # 'google', 'microsoft', 'github'
    provider_subject = Column(String(255), nullable=False)  # Unique ID from provider
    email_at_provider = Column(String(255), nullable=False)  # Email from provider
    created_at = Column(DateTime, default=utc_now, nullable=False)
    last_used_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="identity_providers")

    __table_args__ = (
        # Ensure each provider account can only be linked once
        Index("uq_provider_subject", "provider_name", "provider_subject", unique=True),
    )
