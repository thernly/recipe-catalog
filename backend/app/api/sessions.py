"""
Active login sessions (account settings).

A session is one live refresh-token row: rotation revokes the old row and creates a new
one, so each signed-in browser has exactly one unrevoked, unexpired row. Revoking it
signs that browser out once its short-lived access token expires.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.logging import get_logger
from app.core.security import hash_token
from app.models._utils import is_expired, utc_now
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.session import SessionRead


router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=list[SessionRead])
async def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's signed-in browsers, most recently active first."""
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.user_id == current_user.id, RefreshToken.revoked.is_(False))
        .order_by(RefreshToken.created_at.desc(), RefreshToken.id.desc())
    )
    cookie = request.cookies.get("refresh_token")
    current_hash = hash_token(cookie) if cookie else None
    return [
        SessionRead(
            id=row.id,
            user_agent=row.user_agent,
            last_active_at=row.created_at,
            current=row.token == current_hash,
        )
        for row in result.scalars()
        if not is_expired(row.expires_at)
    ]


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sign out one of the current user's sessions."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.id == session_id,
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked.is_(False),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    row.revoked = True
    row.revoked_at = utc_now()
    await db.commit()

    logger.info("session_revoked", user_id=current_user.id, session_id=session_id)
