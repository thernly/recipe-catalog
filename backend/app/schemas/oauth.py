"""OAuth/OIDC schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProviderInfo(BaseModel):
    """Information about an available OAuth provider."""

    name: str
    display_name: str
    icon: str


class LinkedProviderResponse(BaseModel):
    """Response model for a linked identity provider."""

    id: int
    provider_name: str
    email_at_provider: str
    created_at: datetime
    last_used_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback."""

    code: str
    state: str
    error: str | None = None
    error_description: str | None = None
