"""
Import API endpoints
Allows users to import recipes from JSON files in Schema.org format
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.models.collection import Collection, RecipeCollection
from app.models.household import Household
from app.models.recipe import Recipe
from app.models.user import User
from app.utils.file_validation import validate_file_size
from app.utils.recipe_format import convert_from_schema_org


router = APIRouter()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


async def _validate_collection(
    collection_id: int | None,
    user_id: int,
    db: AsyncSession,
) -> Collection | None:
    """
    Validate and retrieve a collection if collection_id is provided.

    Args:
        collection_id: Optional collection ID to validate
        user_id: ID of the user who must own the collection
        db: Database session

    Returns:
        Collection object if found, None if collection_id is None

    Raises:
        HTTPException: If collection_id is provided but collection not found
    """
    if not collection_id:
        return None

    result = await db.execute(
        select(Collection).where(Collection.id == collection_id).where(Collection.user_id == user_id)
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    return collection


async def _commit_import_results(db: AsyncSession) -> None:
    """
    Commit import results to the database with error handling.

    Args:
        db: Database session

    Raises:
        HTTPException: If commit fails
    """
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save recipes: {str(e)}")


async def _import_recipes_internal(
    recipes_data: list[dict[str, Any]],
    user_id: int,
    household_id: int,
    duplicate_handling: Literal["skip", "update", "create"],
    collection: Collection | None,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Internal helper function to import recipes from data.

    Args:
        recipes_data: List of recipe dictionaries in Schema.org format
        user_id: ID of the user importing recipes
        household_id: ID of the user's household
        duplicate_handling: How to handle duplicates ("skip", "update", or "create")
        collection: Optional collection to add recipes to
        db: Database session

    Returns:
        Dictionary containing import results and statistics
    """
    # Track import results
    results = {
        "total": len(recipes_data),
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
    }

    # Process each recipe
    for idx, recipe_data in enumerate(recipes_data):
        try:
            # Convert from Schema.org format to internal format
            recipe_dict = convert_from_schema_org(recipe_data)

            # Check for duplicate by name
            existing_recipe = None
            if duplicate_handling in ["skip", "update"]:
                result = await db.execute(
                    select(Recipe)
                    .where(Recipe.user_id == user_id)
                    .where(Recipe.name == recipe_dict["name"])
                    .where(Recipe.deleted_at.is_(None))
                )
                existing_recipe = result.scalar_one_or_none()

            if existing_recipe:
                if duplicate_handling == "skip":
                    results["skipped"] += 1
                    continue
                elif duplicate_handling == "update":
                    # Update existing recipe
                    existing_recipe.description = recipe_dict["description"]
                    existing_recipe.image_url = recipe_dict["image_url"]
                    existing_recipe.recipe_data = recipe_dict["recipe_data"]
                    existing_recipe.source_url = recipe_dict["source_url"]
                    existing_recipe.cuisine = recipe_dict["cuisine"]
                    existing_recipe.category = recipe_dict["category"]
                    existing_recipe.total_time_minutes = recipe_dict["total_time_minutes"]
                    existing_recipe.is_modified = True
                    existing_recipe.updated_at = datetime.now(UTC)

                    results["updated"] += 1
                    recipe_to_add = existing_recipe
            else:
                # Create new recipe
                new_recipe = Recipe(
                    user_id=user_id,
                    household_id=household_id,
                    name=recipe_dict["name"],
                    description=recipe_dict["description"],
                    image_url=recipe_dict["image_url"],
                    recipe_data=recipe_dict["recipe_data"],
                    source_url=recipe_dict["source_url"],
                    source_type=recipe_dict["source_type"],
                    cuisine=recipe_dict["cuisine"],
                    category=recipe_dict["category"],
                    total_time_minutes=recipe_dict["total_time_minutes"],
                    imported_at=datetime.now(UTC),
                )
                db.add(new_recipe)
                results["created"] += 1
                recipe_to_add = new_recipe

            # Add to collection if specified
            if collection and recipe_to_add:
                # Flush to get the recipe ID if it's new
                await db.flush()

                # Check if recipe is already in collection
                existing_link = await db.execute(
                    select(RecipeCollection)
                    .where(RecipeCollection.recipe_id == recipe_to_add.id)
                    .where(RecipeCollection.collection_id == collection.id)
                )
                if not existing_link.scalar_one_or_none():
                    db.add(RecipeCollection(recipe_id=recipe_to_add.id, collection_id=collection.id))

        except (ValueError, KeyError, TypeError) as e:
            # Handle expected validation and format errors
            results["failed"] += 1
            results["errors"].append(
                {
                    "index": idx,
                    "name": recipe_data.get("name", "Unknown"),
                    "error": str(e),
                }
            )
        except Exception:
            # Log unexpected errors and re-raise
            logger.exception(f"Unexpected error during import at index {idx}")
            raise

    return results


@router.post("/recipes")
@limiter.limit("20000/hour")
async def import_recipes(
    request: Request,
    file: UploadFile = File(...),
    duplicate_handling: Literal["skip", "update", "create"] = Form("skip"),
    collection_id: int = Form(None),
    current_user: User = Depends(get_current_user),
    household: "Household" = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Import recipes from a JSON file in Schema.org Recipe format.

    Args:
        file: JSON file containing recipes (can be single recipe object or array of recipes)
        duplicate_handling: How to handle duplicate recipes (by name)
            - skip: Skip recipes with matching names
            - update: Update existing recipes with matching names
            - create: Always create new recipes (allow duplicates)
        collection_id: Optional collection ID to add imported recipes to
        current_user: Current authenticated user
        db: Database session

    Returns:
        Summary of import results
    """
    # Validate file size
    await validate_file_size(file)

    # Validate file type
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="File must be a JSON file")

    # Read and parse JSON
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    # Normalize to array of recipes
    if isinstance(data, dict):
        # Single recipe object
        recipes_data = [data]
    elif isinstance(data, list):
        # Array of recipes
        recipes_data = data
    else:
        raise HTTPException(status_code=400, detail="JSON must be a recipe object or array of recipes")

    # Validate collection if specified
    collection = await _validate_collection(collection_id, current_user.id, db)

    # Import recipes using shared helper function
    results = await _import_recipes_internal(
        recipes_data=recipes_data,
        user_id=current_user.id,
        household_id=household.id,
        duplicate_handling=duplicate_handling,
        collection=collection,
        db=db,
    )

    # Commit all changes
    await _commit_import_results(db)

    return {
        "success": True,
        "message": f"Imported {results['created']} new recipes, updated {results['updated']}, skipped {results['skipped']}, failed {results['failed']}",
        "details": results,
    }


@router.post("/recipes/json")
@limiter.limit("20000/hour")
async def import_recipes_json(
    request: Request,
    recipes: list[dict[str, Any]],
    duplicate_handling: Literal["skip", "update", "create"] = "skip",
    collection_id: int = None,
    current_user: User = Depends(get_current_user),
    household: "Household" = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Import recipes from JSON data (for API/extension use).

    Args:
        recipes: Array of recipe objects in Schema.org format
        duplicate_handling: How to handle duplicate recipes
        collection_id: Optional collection ID to add recipes to
        current_user: Current authenticated user
        db: Database session

    Returns:
        Summary of import results
    """
    # Validate collection if specified
    collection = await _validate_collection(collection_id, current_user.id, db)

    # Import recipes using shared helper function
    results = await _import_recipes_internal(
        recipes_data=recipes,
        user_id=current_user.id,
        household_id=household.id,
        duplicate_handling=duplicate_handling,
        collection=collection,
        db=db,
    )

    # Commit all changes
    await _commit_import_results(db)

    return {
        "success": True,
        "message": f"Imported {results['created']} new recipes, updated {results['updated']}, skipped {results['skipped']}, failed {results['failed']}",
        "details": results,
    }
