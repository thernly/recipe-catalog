"""
Recipe CRUD operations.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.core.exceptions import InvalidInputError, RecipeNotFoundError
from app.core.security import sanitize_html
from app.models.collection import RecipeCollection
from app.models.household import Household
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.recipe import Recipe as RecipeSchema
from app.schemas.recipe import RecipeCreate, RecipeSummary, RecipeUpdate


router = APIRouter()


def sanitize_recipe_data(data: dict) -> dict:
    """
    Recursively sanitize string values in recipe data dictionary.

    Args:
        data: Dictionary containing recipe data

    Returns:
        Dictionary with sanitized string values
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_html(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_recipe_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_recipe_data(item)
                if isinstance(item, dict)
                else sanitize_html(item)
                if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


@router.post("/", response_model=RecipeSchema, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new recipe.

    Args:
        recipe_data: Recipe creation data
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        Recipe: The created recipe
    """
    # Sanitize user input to prevent XSS attacks
    sanitized_name = sanitize_html(recipe_data.name) if recipe_data.name else None
    sanitized_description = (
        sanitize_html(recipe_data.description) if recipe_data.description else None
    )
    sanitized_recipe_data = sanitize_recipe_data(recipe_data.recipe_data)

    # Create recipe
    new_recipe = Recipe(
        user_id=current_user.id,
        household_id=household.id,
        name=sanitized_name,
        description=sanitized_description,
        image_url=recipe_data.image_url,
        recipe_data=sanitized_recipe_data,
        source_url=recipe_data.source_url,
        source_type=recipe_data.source_type,
        cuisine=recipe_data.cuisine,
        category=recipe_data.category,
        total_time_minutes=recipe_data.total_time_minutes,
        imported_at=datetime.now(UTC) if recipe_data.source_type == "imported" else None,
    )

    db.add(new_recipe)
    await db.flush()

    # Add to collections if specified
    if recipe_data.collection_ids:
        for collection_id in recipe_data.collection_ids:
            recipe_collection = RecipeCollection(
                recipe_id=new_recipe.id, collection_id=collection_id
            )
            db.add(recipe_collection)

    await db.commit()
    await db.refresh(new_recipe)

    # Convert to Pydantic model and add creator display name
    recipe_response = RecipeSchema.model_validate(new_recipe)
    recipe_response.creator_display_name = current_user.display_name

    return recipe_response


@router.get("/{recipe_id}", response_model=RecipeSchema)
async def get_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single recipe by ID.

    Args:
        recipe_id: Recipe ID
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        Recipe: The requested recipe

    Raises:
        HTTPException: If recipe not found or unauthorized
    """
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.household_id == household.id)
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise RecipeNotFoundError(recipe_id=recipe_id)

    # Get creator display name
    user_result = await db.execute(select(User).where(User.id == recipe.user_id))
    creator = user_result.scalar_one_or_none()

    # Convert to Pydantic model and add creator info
    recipe_response = RecipeSchema.model_validate(recipe)
    recipe_response.creator_display_name = creator.display_name if creator else None

    # TODO: Track recipe view for "recently viewed" feature

    return recipe_response


@router.patch("/{recipe_id}", response_model=RecipeSchema)
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a recipe.

    Args:
        recipe_id: Recipe ID
        recipe_update: Recipe update data
        current_user: The authenticated user
        db: Database session

    Returns:
        Recipe: The updated recipe

    Raises:
        HTTPException: If recipe not found or unauthorized
    """
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.user_id == current_user.id)
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise RecipeNotFoundError(recipe_id=recipe_id)

    # Update fields with sanitization
    update_data = recipe_update.model_dump(exclude_unset=True, exclude={"collection_ids"})

    # Sanitize text fields
    if "name" in update_data and update_data["name"]:
        update_data["name"] = sanitize_html(update_data["name"])
    if "description" in update_data and update_data["description"]:
        update_data["description"] = sanitize_html(update_data["description"])
    if "recipe_data" in update_data and update_data["recipe_data"]:
        update_data["recipe_data"] = sanitize_recipe_data(update_data["recipe_data"])

    for field, value in update_data.items():
        setattr(recipe, field, value)

    # Mark as modified if it was imported
    if recipe.source_type == "imported":
        recipe.is_modified = True

    # Update collections if specified
    if recipe_update.collection_ids is not None:
        # Remove existing collections
        await db.execute(select(RecipeCollection).where(RecipeCollection.recipe_id == recipe_id))

        # Add new collections
        for collection_id in recipe_update.collection_ids:
            recipe_collection = RecipeCollection(recipe_id=recipe.id, collection_id=collection_id)
            db.add(recipe_collection)

    await db.commit()
    await db.refresh(recipe)

    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    permanent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a recipe (soft delete by default).

    Args:
        recipe_id: Recipe ID
        permanent: If True, permanently delete; otherwise soft delete
        current_user: The authenticated user
        db: Database session

    Raises:
        HTTPException: If recipe not found or unauthorized
    """
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.user_id == current_user.id)
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise RecipeNotFoundError(recipe_id=recipe_id)

    if permanent:
        # Permanent delete
        await db.delete(recipe)
    else:
        # Soft delete
        recipe.deleted_at = datetime.now(UTC)

    await db.commit()


@router.post("/{recipe_id}/restore", response_model=RecipeSchema)
async def restore_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a soft-deleted recipe.

    Args:
        recipe_id: Recipe ID
        current_user: The authenticated user
        db: Database session

    Returns:
        Recipe: The restored recipe

    Raises:
        HTTPException: If recipe not found or not deleted
    """
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.user_id == current_user.id)
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise RecipeNotFoundError(recipe_id=recipe_id)

    if recipe.deleted_at is None:
        raise InvalidInputError(message="Recipe is not deleted")

    recipe.deleted_at = None
    await db.commit()
    await db.refresh(recipe)

    return recipe


@router.post(
    "/{recipe_id}/duplicate",
    response_model=RecipeSchema,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Duplicate a recipe.

    Args:
        recipe_id: Recipe ID to duplicate
        current_user: The authenticated user
        db: Database session

    Returns:
        Recipe: The duplicated recipe

    Raises:
        HTTPException: If recipe not found
    """
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.user_id == current_user.id,
            Recipe.deleted_at.is_(None),
        )
    )
    original_recipe = result.scalar_one_or_none()

    if not original_recipe:
        raise RecipeNotFoundError(recipe_id=recipe_id)

    # Create duplicate
    duplicate = Recipe(
        user_id=current_user.id,
        name=f"{original_recipe.name} (Copy)",
        description=original_recipe.description,
        image_url=original_recipe.image_url,
        recipe_data=original_recipe.recipe_data,
        source_url=original_recipe.source_url,
        source_type="manual",  # Duplicates are always manual
        cuisine=original_recipe.cuisine,
        category=original_recipe.category,
        total_time_minutes=original_recipe.total_time_minutes,
    )

    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)

    return duplicate
