"""
Import API endpoints
Allows users to import recipes from JSON files in Schema.org format
"""

import json
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.core.exceptions import AppException, ErrorCode, InvalidInputError
from app.core.logging import get_logger
from app.models._utils import ensure_utc, utc_now
from app.models.collection import Collection, RecipeCollection
from app.models.household import Household
from app.models.recipe import Recipe
from app.models.recipe_note import RecipeNote, note_author_name
from app.models.user import User
from app.services.recipe_cleanup import clean_recipe_data, derive_total_time_minutes
from app.utils.file_validation import validate_file_size
from app.utils.recipe_format import convert_from_schema_org, plain_text
from app.utils.urls import safe_http_url


router = APIRouter()
logger = get_logger(__name__)
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
        select(Collection)
        .where(Collection.id == collection_id)
        .where(Collection.user_id == user_id)
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
        logger.exception("import_commit_failed")
        raise AppException("Failed to save recipes", ErrorCode.INTERNAL_ERROR) from e


async def _restore_notes(
    recipe: Recipe,
    notes: list[dict[str, Any]],
    user_id: int,
    is_new: bool,
    db: AsyncSession,
) -> None:
    """Add a file's notes to a created or updated recipe, skipping any already there.

    A note matches when its author name, timestamp and text are all the same, so
    importing the same file twice adds nothing the second time.
    """
    if not notes:
        return
    seen: set[tuple[str, datetime, str]] = set()
    if not is_new:
        rows = await db.execute(
            select(RecipeNote)
            .where(RecipeNote.recipe_id == recipe.id)
            .options(selectinload(RecipeNote.user))
        )
        seen = {(note_author_name(n), ensure_utc(n.created_at), n.text) for n in rows.scalars()}
    for note in notes:
        created_at = note["created_at"] or utc_now()
        key = (note["author_name"], created_at, note["text"])
        if key in seen:
            continue
        seen.add(key)
        db.add(
            RecipeNote(
                recipe_id=recipe.id,
                user_id=user_id,
                author_name=note["author_name"],
                text=note["text"],
                created_at=created_at,
            )
        )


def _url_key(url: str | None) -> str | None:
    """
    A source web address reduced to what identifies the page, for duplicate matching.

    ponytail: drops only the #fragment and a trailing slash; addresses that differ in
    tracking parameters (?utm_source=...) or http/https still count as different pages.
    """
    return url.split("#")[0].rstrip("/") or None if url else None


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
        Dictionary containing import results and statistics. `items` has one entry per
        recipe that did not fail: its index, status (created, updated or skipped) and
        recipe id (the existing recipe's id when skipped).
    """
    if len(recipes_data) > 500:
        raise InvalidInputError("At most 500 recipes may be imported at once")
    # Track import results
    results: dict[str, Any] = {
        "total": len(recipes_data),
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
        "items": [],
    }

    names = {
        plain_text(entry["name"])[:500]
        for entry in recipes_data
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    url_keys = {
        key
        for entry in recipes_data
        if isinstance(entry, dict) and (key := _url_key(safe_http_url(entry.get("url"))))
    }
    # A duplicate is a recipe with the same source web address, else the same name
    existing_by_name: dict[Any, Recipe] = {}
    existing_by_url: dict[str, Recipe] = {}
    if duplicate_handling in ("skip", "update"):
        rows = await db.execute(
            select(Recipe)
            .where(
                Recipe.user_id == user_id,
                Recipe.deleted_at.is_(None),
                or_(
                    Recipe.name.in_(names),
                    Recipe.source_url.in_(url_keys | {f"{key}/" for key in url_keys}),
                ),
            )
            .order_by(Recipe.id)
        )
        for recipe in rows.scalars():
            existing_by_name.setdefault(recipe.name, recipe)
            if key := _url_key(recipe.source_url):
                existing_by_url.setdefault(key, recipe)
    linked_ids: set[Any] = set()
    if collection:
        linked_ids = set(
            (
                await db.execute(
                    select(RecipeCollection.recipe_id).where(
                        RecipeCollection.collection_id == collection.id
                    )
                )
            )
            .scalars()
            .all()
        )

    # Process each recipe
    for idx, recipe_data in enumerate(recipes_data):
        try:
            # Convert from Schema.org format to internal format
            recipe_dict = await convert_from_schema_org(recipe_data)

            url_key = _url_key(recipe_dict["source_url"])
            existing_recipe = (existing_by_url.get(url_key) if url_key else None) or (
                existing_by_name.get(recipe_dict["name"])
            )

            if not (existing_recipe and duplicate_handling == "skip"):
                # Shared cleanup: yield, times, parsedIngredients. On update, keep the
                # existing recipe's model-parsed lines for unchanged ingredient text.
                stored: dict[str, Any] = (
                    existing_recipe.recipe_data
                    if existing_recipe and isinstance(existing_recipe.recipe_data, dict)
                    else {}
                )
                previous_parsed = stored.get("parsedIngredients")
                cleaned = clean_recipe_data(recipe_dict["recipe_data"], previous_parsed)
                recipe_dict["recipe_data"] = cleaned.data
                recipe_dict["total_time_minutes"] = derive_total_time_minutes(cleaned.data)

            if existing_recipe:
                if duplicate_handling == "skip":
                    results["skipped"] += 1
                    results["items"].append(
                        {"index": idx, "status": "skipped", "recipe_id": existing_recipe.id}
                    )
                    continue
                elif duplicate_handling == "update":
                    # Update existing recipe (a match by web address may bring a new name)
                    existing_recipe.name = recipe_dict["name"]
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
                    results["items"].append(
                        {"index": idx, "status": "updated", "recipe_id": existing_recipe.id}
                    )
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
                # Flush to assign the id reported in items
                await db.flush()
                if duplicate_handling in ("skip", "update"):
                    existing_by_name[new_recipe.name] = new_recipe
                    if url_key:
                        existing_by_url[url_key] = new_recipe
                results["created"] += 1
                recipe_to_add = new_recipe
                results["items"].append(
                    {"index": idx, "status": "created", "recipe_id": new_recipe.id}
                )

            await _restore_notes(
                recipe_to_add,
                recipe_dict["notes"],
                user_id,
                is_new=recipe_to_add is not existing_recipe,
                db=db,
            )

            # Add to collection if specified
            if collection and recipe_to_add:
                # Flush to get the recipe ID if it's new
                await db.flush()

                if recipe_to_add.id not in linked_ids:
                    db.add(
                        RecipeCollection(recipe_id=recipe_to_add.id, collection_id=collection.id)
                    )
                    linked_ids.add(recipe_to_add.id)

        except (ValueError, KeyError, TypeError) as e:
            # Handle expected validation and format errors
            results["failed"] += 1
            results["errors"].append(
                {
                    "index": idx,
                    "name": recipe_data.get("name", "Unknown")
                    if isinstance(recipe_data, dict)
                    else "Unknown",
                    "error": str(e),
                }
            )
        except Exception:
            # Log unexpected errors and re-raise
            logger.exception("recipe_import_failed", index=idx)
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
        duplicate_handling: How to handle duplicate recipes (same source web
            address, or same name)
            - skip: Skip recipes that match an existing one
            - update: Update the existing recipe that matches
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
    if not file.filename or not file.filename.lower().endswith(".json"):
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
        raise HTTPException(
            status_code=400, detail="JSON must be a recipe object or array of recipes"
        )

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
