"""Personal API token schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiTokenCreate(BaseModel):
    """Request body for creating a personal API token."""

    name: str = Field(..., min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name must not be blank")
        return v


class ApiTokenRead(BaseModel):
    """A token as listed in settings. Never includes the token value."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    token_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None


class ApiTokenCreated(ApiTokenRead):
    """Response to token creation: the only time the plain token is returned."""

    token: str
