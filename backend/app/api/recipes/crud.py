"""
Recipe CRUD operations.
"""

import base64
import binascii
import hashlib
import io
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, Response, status
from PIL import Image
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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
from app.services.categories import known_categories, normalize_categories, set_categories
from app.services.recipe_cleanup import clean_recipe_data, derive_total_time_minutes
from app.utils.recipe_format import MAX_IMAGES


router = APIRouter()


MAX_UPLOADED_PHOTO_BYTES = 300 * 1024
PHOTO_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


def uploaded_photo(image: Any) -> dict[str, str] | None:
    """A photo added in the form, checked; None when it is not one.

    It has no address, only base64 data (shrunk in the browser) that must decode to at
    most MAX_UPLOADED_PHOTO_BYTES of a real JPEG, PNG or WebP picture.
    """
    if not isinstance(image, dict) or image.get("url") or not isinstance(image.get("data"), str):
        return None
    data = image["data"]
    if len(data) > (MAX_UPLOADED_PHOTO_BYTES + 2) // 3 * 4:
        return None
    try:
        raw = base64.b64decode(data, validate=True)
        with Image.open(io.BytesIO(raw)) as picture:
            mime_type = PHOTO_FORMATS.get(picture.format or "")
            picture.verify()
    except (binascii.Error, ValueError, OSError, Image.DecompressionBombError):
        return None
    if mime_type is None or mime_type not in settings.ALLOWED_IMAGE_TYPES:
        return None
    return {"url": "", "data": data, "mimeType": mime_type}


def keep_stored_images(incoming: dict[str, Any], stored: dict[str, Any]) -> dict[str, Any]:
    """The recipe's photos after an edit: stored ones removed or reordered, plus uploads.

    Pictures with an address arrive through imports, which fetch and check them. A request
    may drop or reorder the stored photos (matched by address and data) and add photos
    taken or picked in the form (see uploaded_photo). Without an `images` list the stored
    photos are kept.
    """
    stored_images = [image for image in stored.get("images") or [] if isinstance(image, dict)]
    if "images" not in incoming:
        return {**incoming, "images": stored_images} if stored_images else incoming
    requested = incoming["images"]
    if not isinstance(requested, list) or len(requested) > MAX_IMAGES:
        raise InvalidInputError(message=f"A recipe can have at most {MAX_IMAGES} photos")
    by_key = {(image.get("url"), image.get("data")): image for image in stored_images}
    kept: list[dict[str, Any]] = []
    for image in requested:
        match = (
            by_key.get((image.get("url"), image.get("data"))) if isinstance(image, dict) else None
        ) or uploaded_photo(image)
        if match is None:
            raise InvalidInputError(
                message="A new photo must be a JPEG, PNG or WebP picture of 300 KB or less"
            )
        key = (match.get("url"), match.get("data"))
        if not any((k.get("url"), k.get("data")) == key for k in kept):
            kept.append(match)
    return {**incoming, "images": kept}


def sanitize_recipe_data(data: dict[str, Any]) -> dict[str, Any]:
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

    result = await db.execute(select(Collection).where(Collection.id.in_(collection_ids)))
    collections = {collection.id: collection for collection in result.scalars()}
    for collection_id in dict.fromkeys(collection_ids):
        collection = collections.get(collection_id)
        if not collection:
            raise InvalidInputError(message=f"Collection {collection_id} not found")
        if collection.user_id != user_id and collection.household_id != household_id:
            raise InvalidInputError(
                message=f"Collection {collection_id} does not belong to you or your household"
            )


@router.post(
    "/",
    response_model=RecipeSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Recipe successfully created"},
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "unauthorized",
                        "message": "Not authenticated",
                        "details": {},
                    }
                }
            },
        },
        400: {
            "description": "Invalid collection ID or validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "invalid_input",
                        "message": "Collection 123 does not belong to you or your household",
                        "details": {},
                    }
                }
            },
        },
        422: {
            "description": "Validation error - invalid request format",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "validation_error",
                        "message": "Validation error",
                        "details": {"errors": [{"field": "name", "message": "Field required"}]},
                    }
                }
            },
        },
    },
)
async def create_recipe(
    recipe_data: RecipeCreate,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new recipe.

    Creates a new recipe in the authenticated user's household. The recipe can optionally be
    added to one or more collections that the user owns or belongs to their household.

    **Authentication:** Required (Bearer token)

    **Rate Limit:** None

    Args:
        recipe_data: Recipe creation data (name, ingredients, instructions, etc.)
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        Recipe: The created recipe object

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 400: If collection_ids contains IDs not owned by user/household
        HTTPException 422: If request data is invalid
    """
    # name/description are already stripped to plain text by the RecipeCreate validator
    sanitized_name = recipe_data.name or None
    sanitized_description = recipe_data.description or None
    # Shared cleanup: yield, times, parsedIngredients
    # A new recipe has no stored photos to keep, only uploaded ones
    cleaned_recipe_data = clean_recipe_data(
        keep_stored_images(sanitize_recipe_data(recipe_data.recipe_data), {})
    ).data
    total_time_minutes = recipe_data.total_time_minutes
    if total_time_minutes is None:
        total_time_minutes = derive_total_time_minutes(cleaned_recipe_data)

    # Create recipe
    new_recipe = Recipe(
        user_id=current_user.id,
        household_id=household.id,
        name=sanitized_name,
        description=sanitized_description,
        image_url=recipe_data.image_url,
        recipe_data=cleaned_recipe_data,
        source_url=recipe_data.source_url,
        source_type=recipe_data.source_type,
        cuisine=recipe_data.cuisine,
        total_time_minutes=total_time_minutes,
        imported_at=datetime.now(UTC) if recipe_data.source_type == "imported" else None,
    )
    known = await known_categories(current_user.id, db)
    set_categories(new_recipe, normalize_categories(recipe_data.categories, known))

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

        for collection_id in dict.fromkeys(recipe_data.collection_ids):
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
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.household_id == household.id,
            or_(Recipe.deleted_at.is_(None), Recipe.user_id == current_user.id),
        )
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


@router.get("/{recipe_id}/photo", response_class=Response)
async def get_recipe_photo(
    recipe_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """The recipe's main photo as an image file, from its stored picture data.

    Lists show photos through this rather than the picture's address on the recipe's
    site, which can disappear. Readable by whoever can read the recipe. Revalidated on
    every view (ETag), so a new main photo shows at once.
    """
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.household_id == household.id,
            or_(Recipe.deleted_at.is_(None), Recipe.user_id == current_user.id),
        )
    )
    recipe = result.scalar_one_or_none()
    photo = recipe.main_photo if recipe else None
    # Only image types are served, so stored data can never be sent as a page or script
    if photo is None or photo.get("mimeType") not in settings.ALLOWED_IMAGE_TYPES:
        raise RecipeNotFoundError(recipe_id=recipe_id)
    try:
        content = base64.b64decode(photo["data"], validate=True)
    except (binascii.Error, ValueError) as error:
        raise RecipeNotFoundError(recipe_id=recipe_id) from error

    etag = f'"{hashlib.sha256(content).hexdigest()[:32]}"'
    headers = {"ETag": etag, "Cache-Control": "private, no-cache"}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return Response(content, media_type=photo["mimeType"], headers=headers)


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
        select(Recipe).where(
            Recipe.id == recipe_id, Recipe.user_id == current_user.id, Recipe.deleted_at.is_(None)
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise RecipeNotFoundError(recipe_id=recipe_id)

    # Update fields with sanitization
    update_data = recipe_update.model_dump(
        exclude_unset=True, exclude={"collection_ids", "categories"}
    )

    # name/description are already stripped to plain text by the RecipeUpdate validator
    if "recipe_data" in update_data and update_data["recipe_data"]:
        # Shared cleanup. Unchanged ingredient lines keep their stored model parses; the
        # previous entries come from the database, never from the request.
        stored: dict[str, Any] = recipe.recipe_data if isinstance(recipe.recipe_data, dict) else {}
        previous_parsed = stored.get("parsedIngredients")
        update_data["recipe_data"] = clean_recipe_data(
            keep_stored_images(sanitize_recipe_data(update_data["recipe_data"]), stored),
            previous_parsed,
        ).data
        if "total_time_minutes" not in update_data:
            derived_total = derive_total_time_minutes(update_data["recipe_data"])
            if derived_total is not None:
                update_data["total_time_minutes"] = derived_total

    for field, value in update_data.items():
        setattr(recipe, field, value)

    # New categories when sent ([] clears them); otherwise the stored ones are written
    # back into recipe_data, so a new recipe_data cannot leave the two out of step
    if recipe_update.categories is not None:
        known = await known_categories(current_user.id, db)
        set_categories(recipe, normalize_categories(recipe_update.categories, known))
    else:
        set_categories(recipe, recipe.category_names)

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
        for collection_id in dict.fromkeys(recipe_update.collection_ids):
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
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Duplicate a recipe. Any household member may copy a household recipe; the copy
    belongs to whoever made it, so they can edit it.

    Args:
        recipe_id: Recipe ID to duplicate
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        Recipe: The duplicated recipe

    Raises:
        HTTPException: If recipe not found
    """
    # A read of the original (household scope); the write below is the user's own row.
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.household_id == household.id,
            Recipe.deleted_at.is_(None),
        )
    )
    original_recipe = result.scalar_one_or_none()

    if not original_recipe:
        raise RecipeNotFoundError(recipe_id=recipe_id)

    # Create duplicate
    duplicate = Recipe(
        user_id=current_user.id,
        household_id=original_recipe.household_id,
        name=f"{original_recipe.name} (Copy)",
        description=original_recipe.description,
        image_url=original_recipe.image_url,
        recipe_data=original_recipe.recipe_data,
        source_url=original_recipe.source_url,
        source_type="manual",  # Duplicates are always manual
        cuisine=original_recipe.cuisine,
        total_time_minutes=original_recipe.total_time_minutes,
    )
    set_categories(duplicate, original_recipe.category_names)

    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)

    return duplicate
