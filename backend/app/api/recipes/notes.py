"""
Recipe notes: dated notes household members leave on a recipe.

Scoping differs from the rest of the recipe API on purpose. Any household member who can
see a recipe may add a note; only the note's author may edit it; the author or the
recipe's owner may delete it. Every route first loads the recipe through the household,
so another household's recipe or note is a 404, never a 403.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.core.exceptions import (
    AppException,
    ErrorCode,
    RecipeNotFoundError,
    UnauthorizedAccessError,
)
from app.models._utils import ensure_utc, utc_now
from app.models.household import Household
from app.models.recipe import Recipe
from app.models.recipe_note import RecipeNote, note_author_name
from app.models.user import User
from app.schemas.recipe_note import RecipeNoteResponse, RecipeNoteWrite


router = APIRouter()


async def _get_recipe(recipe_id: int, household: Household, db: AsyncSession) -> Recipe:
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.household_id == household.id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise RecipeNotFoundError(recipe_id=recipe_id)
    return recipe


async def _get_note(recipe: Recipe, note_id: int, db: AsyncSession) -> RecipeNote:
    result = await db.execute(
        select(RecipeNote)
        .where(RecipeNote.id == note_id, RecipeNote.recipe_id == recipe.id)
        .options(selectinload(RecipeNote.user))
    )
    note = result.scalar_one_or_none()
    if not note:
        raise AppException(
            message="Note not found",
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return note


def _to_response(note: RecipeNote, current_user: User) -> RecipeNoteResponse:
    return RecipeNoteResponse(
        id=note.id,
        recipe_id=note.recipe_id,
        text=note.text,
        author_name=note_author_name(note),
        is_author=note.user_id == current_user.id,
        created_at=ensure_utc(note.created_at),
        updated_at=ensure_utc(note.updated_at) if note.updated_at else None,
    )


@router.get("/{recipe_id}/notes", response_model=list[RecipeNoteResponse])
async def list_notes(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """List a recipe's notes, newest first."""
    recipe = await _get_recipe(recipe_id, household, db)
    result = await db.execute(
        select(RecipeNote)
        .where(RecipeNote.recipe_id == recipe.id)
        .options(selectinload(RecipeNote.user))
        .order_by(RecipeNote.created_at.desc(), RecipeNote.id.desc())
    )
    return [_to_response(note, current_user) for note in result.scalars()]


@router.post(
    "/{recipe_id}/notes",
    response_model=RecipeNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_note(
    recipe_id: int,
    body: RecipeNoteWrite,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """Add a note to a recipe in the caller's household."""
    recipe = await _get_recipe(recipe_id, household, db)
    note = RecipeNote(recipe_id=recipe.id, user_id=current_user.id, text=body.text)
    note.user = current_user
    db.add(note)
    await db.commit()
    return _to_response(note, current_user)


@router.patch("/{recipe_id}/notes/{note_id}", response_model=RecipeNoteResponse)
async def update_note(
    recipe_id: int,
    note_id: int,
    body: RecipeNoteWrite,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """Edit a note's text. Only its author may."""
    recipe = await _get_recipe(recipe_id, household, db)
    note = await _get_note(recipe, note_id, db)
    if note.user_id != current_user.id:
        raise UnauthorizedAccessError(message="Only the note's author can edit it")
    note.text = body.text
    note.updated_at = utc_now()
    await db.commit()
    return _to_response(note, current_user)


@router.delete("/{recipe_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    recipe_id: int,
    note_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """Delete a note. Its author or the recipe's owner may."""
    recipe = await _get_recipe(recipe_id, household, db)
    note = await _get_note(recipe, note_id, db)
    if note.user_id != current_user.id and recipe.user_id != current_user.id:
        raise UnauthorizedAccessError(
            message="Only the note's author or the recipe's owner can delete it"
        )
    await db.delete(note)
    await db.commit()
