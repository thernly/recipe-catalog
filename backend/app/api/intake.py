"""
Recipe intake endpoints for the Recipe Siphon browser extension.

Requests authenticate with a personal API token (`Authorization: Bearer rcat_...`),
or with a normal session. Token-authenticated requests skip the CSRF check (see
`app/middleware/csrf.py`); cookie-authenticated ones do not.

For now intake saves through the same import logic as the file upload, with its
default duplicate handling (`skip` on an exact name match).
"""

from typing import Any, Literal

from fastapi import APIRouter, Body, Depends, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.import_recipes import _commit_import_results, _import_recipes_internal
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_intake_household, get_intake_user
from app.core.exceptions import InvalidInputError
from app.core.logging import get_logger
from app.models.household import Household
from app.models.user import User


router = APIRouter()
logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)


class IntakeResponse(BaseModel):
    """Result of a single-recipe intake."""

    success: bool
    status: Literal["created", "skipped"]
    id: int | None
    message: str
    url: str


class IntakeCheckResponse(BaseModel):
    """Result of a token check."""

    success: bool
    message: str


def _recipe_url(recipe_id: int) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/recipes/{recipe_id}"


@router.get("/check", response_model=IntakeCheckResponse)
async def check_intake_token(current_user: User = Depends(get_intake_user)):
    """Return 200 when the credentials are valid (401 otherwise, via the dependency)."""
    return IntakeCheckResponse(success=True, message="Token is valid")


@router.post("", response_model=IntakeResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_HOUR}/hour")
async def intake_recipe(
    request: Request,
    recipe: dict[str, Any] = Body(...),
    current_user: User = Depends(get_intake_user),
    household: Household = Depends(get_intake_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Import one recipe, sent as a schema.org Recipe JSON object.

    Returns `created` with the new recipe's id, or `skipped` with the id of the
    existing recipe of the same name.
    """
    # Read before any rollback/commit can expire the loaded objects
    user_id = current_user.id

    results = await _import_recipes_internal(
        recipes_data=[recipe],
        user_id=user_id,
        household_id=household.id,
        duplicate_handling="skip",
        collection=None,
        db=db,
    )

    if results["failed"]:
        await db.rollback()
        error = results["errors"][0]["error"]
        logger.info("intake_rejected", user_id=user_id, error=error)
        raise InvalidInputError(message=f"Recipe could not be imported: {error}")

    await _commit_import_results(db)

    item = results["items"][0]
    recipe_id = item["recipe_id"]
    status = item["status"]
    logger.info("intake_saved", user_id=user_id, recipe_id=recipe_id, status=status)

    if status == "created":
        message = "Recipe imported"
    else:
        message = "A recipe with this name already exists; nothing was imported"

    return IntakeResponse(
        success=True,
        status=status,
        id=recipe_id,
        message=message,
        url=_recipe_url(recipe_id),
    )
