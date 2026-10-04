"""
Personal API token endpoints (account settings).

These routes manage tokens and therefore require a normal session: `get_current_user`
does not accept personal API tokens, so a token cannot list, create or revoke tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import MAX_API_TOKENS_PER_USER
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import InvalidInputError
from app.core.logging import get_logger
from app.core.security import sanitize_html
from app.models._utils import utc_now
from app.models.api_token import ApiToken
from app.models.user import User
from app.schemas.api_token import ApiTokenCreate, ApiTokenCreated, ApiTokenRead


router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=list[ApiTokenRead])
async def list_api_tokens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's active (unrevoked) API tokens."""
    result = await db.execute(
        select(ApiToken)
        .where(ApiToken.user_id == current_user.id)
        .where(ApiToken.revoked_at.is_(None))
        .order_by(ApiToken.created_at.desc(), ApiToken.id.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ApiTokenCreated, status_code=status.HTTP_201_CREATED)
async def create_api_token(
    token_in: ApiTokenCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a personal API token for the intake routes.

    The plain token is in this response only; just its hash is stored.
    """
    active_count = await db.scalar(
        select(func.count())
        .select_from(ApiToken)
        .where(ApiToken.user_id == current_user.id)
        .where(ApiToken.revoked_at.is_(None))
    )
    if (active_count or 0) >= MAX_API_TOKENS_PER_USER:
        raise InvalidInputError(
            message=f"You can have at most {MAX_API_TOKENS_PER_USER} active API tokens. "
            "Revoke one before creating another.",
        )

    api_token, raw_token = ApiToken.create_for_user(
        user_id=current_user.id, name=sanitize_html(token_in.name)
    )
    db.add(api_token)
    await db.commit()
    await db.refresh(api_token)

    logger.info("api_token_created", user_id=current_user.id, token_id=api_token.id)

    return ApiTokenCreated(
        id=api_token.id,
        name=api_token.name,
        token_prefix=api_token.token_prefix,
        created_at=api_token.created_at,
        last_used_at=api_token.last_used_at,
        token=raw_token,
    )


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke one of the current user's API tokens. It stops working immediately."""
    result = await db.execute(
        select(ApiToken)
        .where(ApiToken.id == token_id)
        .where(ApiToken.user_id == current_user.id)
        .where(ApiToken.revoked_at.is_(None))
    )
    api_token = result.scalar_one_or_none()
    if api_token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API token not found")

    api_token.revoked_at = utc_now()
    await db.commit()

    logger.info("api_token_revoked", user_id=current_user.id, token_id=token_id)
