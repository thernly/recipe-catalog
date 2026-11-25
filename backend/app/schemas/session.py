"""Active login session schemas."""

from datetime import datetime

from pydantic import BaseModel


class SessionRead(BaseModel):
    """One signed-in browser, as listed in settings. Never includes the token."""

    id: int
    user_agent: str | None
    # Refresh tokens rotate on every refresh, so the live row's creation time is
    # when the session was last active.
    last_active_at: datetime
    current: bool
