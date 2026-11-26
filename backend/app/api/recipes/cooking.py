"""
A recipe's rating and last-cooked date.

Like notes, these belong to the household rather than the recipe's owner: any member
who can see the recipe may set them. The recipe is loaded through the household, so
another household's recipe is a 404.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.recipes.notes import _get_recipe
from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.models.household import Household
from app.models.user import User
from app.schemas.recipe import RecipeCooking


router = APIRouter()


@router.patch("/{recipe_id}/cooking", response_model=RecipeCooking)
async def update_cooking(
    recipe_id: int,
    body: RecipeCooking,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """Set or clear the rating and/or the last-cooked date. Fields left out stay as
    they are."""
    recipe = await _get_recipe(recipe_id, household, db)
    for field in body.model_fields_set:
        setattr(recipe, field, getattr(body, field))
    await db.commit()
    return RecipeCooking.model_validate(recipe, from_attributes=True)
