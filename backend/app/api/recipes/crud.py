"""
Recipe CRUD operations.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import delete, select
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
from app.schemas.recipe import RecipeCreate, RecipeUpdate


router = APIRouter()


def sanitize_recipe_data(data: dict) -> dict:
    """
    Sanitize user-facing text fields in recipe data.

    Only sanitizes fields that may contain user-provided formatted text:
    - recipeInstructions[].text (cooking steps)
    - notes (user notes)

    Other fields (ingredients, yields, times, etc.) are simple text that
    don't require HTML sanitization, improving performance.

    Args:
        data: Dictionary containing recipe data

    Returns:
        Dictionary with sanitized text fields
    """
    if not isinstance(data, dict):
        return data

    sanitized = dict(data)  # Shallow copy

    # Sanitize instruction text fields (users might paste formatted content)
    if "recipeInstructions" in sanitized and isinstance(sanitized["recipeInstructions"], list):
        sanitized_instructions = []
        for instruction in sanitized["recipeInstructions"]:
            if isinstance(instruction, dict) and "text" in instruction:
                sanitized_instruction = dict(instruction)
                sanitized_instruction["text"] = sanitize_html(instruction["text"])
                sanitized_instructions.append(sanitized_instruction)
            else:
                sanitized_instructions.append(instruction)
        sanitized["recipeInstructions"] = sanitized_instructions

    # Sanitize notes field if present
    if "notes" in sanitized and isinstance(sanitized["notes"], str):
        sanitized["notes"] = sanitize_html(sanitized["notes"])

    return sanitized


async def validate_collection_ownership(
    collection_ids: list[int],
    user_id: int,
    household_id: int,
    db: AsyncSession,
) -> None:
    """
    Validate that all collection IDs belong to the current user or their household.

    Args:
        collection_ids: List of collection IDs to validate
        user_id: Current user's ID
        household_id: Current user's household ID
        db: Database session

    Raises:
        InvalidInputError: If any collection doesn't belong to user or household
    """
    from app.models.collection import Collection

    for collection_id in collection_ids:
        result = await db.execute(
            select(Collection).where(Collection.id == collection_id)
        )
        collection = result.scalar_one_or_none()

        if not collection:
            raise InvalidInputError(message=f"Collection {collection_id} not found")

        # Check if collection belongs to user or their household
        if collection.user_id != user_id and collection.household_id != household_id:
            raise InvalidInputError(
                message=f"Collection {collection_id} does not belong to you or your household"
            )


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
        # Validate that all collections belong to user or household
        await validate_collection_ownership(
            recipe_data.collection_ids,
            current_user.id,
            household.id,
            db,
        )

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
        # Validate that all collections belong to user or household
        if recipe_update.collection_ids:
            # Get household_id from recipe
            await validate_collection_ownership(
                recipe_update.collection_ids,
                current_user.id,
                recipe.household_id,
                db,
            )

        # Remove existing collections
        await db.execute(delete(RecipeCollection).where(RecipeCollection.recipe_id == recipe_id))

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
