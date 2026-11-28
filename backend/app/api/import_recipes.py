"""
Import API endpoints
Allows users to import recipes from JSON files in Schema.org format
"""

import contextlib
import json
from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import MAX_FETCHED_PAGE_BYTES
from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.core.exceptions import AppException, ErrorCode, InvalidInputError
from app.core.logging import get_logger
from app.models._utils import ensure_utc, utc_now
from app.models.collection import Collection, RecipeCollection
from app.models.household import Household
from app.models.meal_plan import MealPlan, PlannedMeal
from app.models.recipe import Recipe
from app.models.recipe_note import RecipeNote, note_author_name
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.user import User
from app.services.categories import known_categories, normalize_categories, set_categories
from app.services.recipe_cleanup import clean_recipe_data, derive_total_time_minutes
from app.services.recipe_page import extract_recipe
from app.utils.file_validation import validate_file_size
from app.utils.recipe_format import convert_from_schema_org, convert_to_schema_org, plain_text
from app.utils.safe_fetch import SafeFetchError, safe_fetch
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
    skip_household_matches: bool = False,
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
        skip_household_matches: With "skip", also treat another household member's
            recipe as the duplicate (restore uses this, so a household backup does
            not copy housemates' recipes). Never with "update": edits are owner-only.

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
        match_household = skip_household_matches and duplicate_handling == "skip"
        rows = await db.execute(
            select(Recipe)
            .where(
                Recipe.household_id == household_id
                if match_household
                else Recipe.user_id == user_id,
                Recipe.deleted_at.is_(None),
                or_(
                    Recipe.name.in_(names),
                    Recipe.source_url.in_(url_keys | {f"{key}/" for key in url_keys}),
                ),
            )
            # The importer's own recipe wins over a housemate's with the same name
            .order_by(Recipe.user_id != user_id, Recipe.id)
        )
        for recipe in rows.scalars():
            existing_by_name.setdefault(recipe.name, recipe)
            if key := _url_key(recipe.source_url):
                existing_by_url.setdefault(key, recipe)
    known = await known_categories(user_id, db)
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
                    set_categories(
                        existing_recipe, normalize_categories(recipe_dict["categories"], known)
                    )
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
                    total_time_minutes=recipe_dict["total_time_minutes"],
                    imported_at=datetime.now(UTC),
                )
                set_categories(new_recipe, normalize_categories(recipe_dict["categories"], known))
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


class UrlImportRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)


@router.post("/url")
@limiter.limit("60/hour")
async def import_recipe_from_url(
    request: Request,
    body: UrlImportRequest,
    current_user: User = Depends(get_current_user),
    household: "Household" = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Save the recipe on a web page, given its address.

    The server fetches the page through `safe_fetch` and imports the schema.org Recipe
    the page embeds (JSON-LD). A recipe already saved from the same address, or with the
    same name, is skipped. Returns `status` (`created` or `skipped`), the recipe `id` and
    a `message`.
    """
    # Read before any rollback/commit can expire the loaded objects
    user_id = current_user.id

    url = safe_http_url(body.url.strip())
    if not url:
        raise InvalidInputError("Enter a web address that starts with http:// or https://")

    try:
        page = await safe_fetch(
            url,
            max_bytes=MAX_FETCHED_PAGE_BYTES,
            allowed_content_types=("text/html", "application/xhtml+xml"),
        )
    except SafeFetchError as e:
        logger.info("url_import_fetch_failed", user_id=user_id, reason=str(e))
        raise InvalidInputError(
            "That page could not be opened. Check the address; some sites also block "
            "automated visits."
        ) from e

    # ponytail: assumes UTF-8 (nearly every recipe site); other encodings import with
    # odd characters. Read the charset from the response if that turns up.
    recipe = extract_recipe(page.content.decode("utf-8", errors="replace"))
    if recipe is None:
        logger.info("url_import_no_recipe", user_id=user_id)
        raise InvalidInputError(
            "No recipe was found on that page. It may not publish its recipe in the "
            "standard format; the Recipe Siphon browser extension can often still save it."
        )
    # The address the page was finally served from, so the same page is one duplicate
    recipe["url"] = page.url

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
        logger.info("url_import_rejected", user_id=user_id, error=error)
        raise InvalidInputError(f"The recipe on that page could not be imported: {error}")

    await _commit_import_results(db)

    item = results["items"][0]
    logger.info(
        "url_import_saved", user_id=user_id, recipe_id=item["recipe_id"], status=item["status"]
    )
    return {
        "status": item["status"],
        "id": item["recipe_id"],
        "message": "Recipe saved"
        if item["status"] == "created"
        else "You already have this recipe (same web address or name); nothing was added",
    }


# ============================================
# Restoring a Complete Backup (`GET /export/all`)
#
# Restore only adds: whatever already exists is kept as it is, so restoring the same
# file twice changes nothing. The file is untrusted input; entries of the wrong shape
# are left out rather than failing the restore.
# ============================================

_BACKUP_RECIPE_FIELDS = ("name", "description", "image_url", "source_url", "cuisine")
_MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack", "other"}
_SOURCE_TYPES = {"imported", "manual", "ai-generated"}
_IMPORT_BATCH = 500  # the importer's own limit per call
_TEXT_LIMIT = 10_000  # for unbounded Text columns


def _text(value: Any, limit: int = _TEXT_LIMIT) -> str | None:
    """A backup's text field cut to its column size; None when blank or not text."""
    return value[:limit] or None if isinstance(value, str) else None


def _dicts(value: Any) -> list[dict[str, Any]]:
    """The objects in a backup's list; anything else in it is dropped."""
    return [entry for entry in value if isinstance(entry, dict)] if isinstance(value, list) else []


async def _restore_backup_recipes(
    entries: list[Any], user_id: int, household_id: int, db: AsyncSession
) -> tuple[dict[str, Any], dict[int, int]]:
    """
    Add the backup's recipes that are not already there.

    Each one goes through the ordinary importer (so `clean_recipe_data` runs and
    duplicates are matched the same way). Returns the importer's results and a map from
    each recipe's id in the file to its id here, for existing and new recipes alike.
    """
    schema_recipes: list[dict[str, Any]] = []
    for entry in entries:
        recipe_data = entry.get("recipe_data") or {} if isinstance(entry, dict) else None
        if not isinstance(recipe_data, dict):
            schema_recipes.append({})  # the importer reports it as failed
            continue
        # A backup made before categories were a list has one `category` string
        categories = entry.get("categories")
        if not isinstance(categories, list):
            categories = [entry.get("category")]
        stored = SimpleNamespace(
            **{field: entry.get(field) for field in _BACKUP_RECIPE_FIELDS},
            recipe_data=recipe_data,
            category_names=[name for name in categories if isinstance(name, str)],
            created_at=None,
        )
        schema = await convert_to_schema_org(stored, fetch_images=False)
        schema["comment"] = entry.get("comment")
        schema_recipes.append(schema)

    results: dict[str, Any] = {
        "total": len(entries),
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
        "items": [],
    }
    for start in range(0, len(schema_recipes), _IMPORT_BATCH):
        part = await _import_recipes_internal(
            recipes_data=schema_recipes[start : start + _IMPORT_BATCH],
            user_id=user_id,
            household_id=household_id,
            duplicate_handling="skip",
            collection=None,
            db=db,
            skip_household_matches=True,
        )
        for key in ("created", "updated", "skipped", "failed"):
            results[key] += part[key]
        for row in (*part["errors"], *part["items"]):
            row["index"] += start
        results["errors"] += part["errors"]
        results["items"] += part["items"]

    id_map: dict[int, int] = {}
    # What the importer does not carry, for each recipe it created
    restored: dict[int, dict[str, Any]] = {}
    for item in results["items"]:
        entry = entries[item["index"]]
        if isinstance(entry.get("id"), int):
            id_map[entry["id"]] = item["recipe_id"]
        if item["status"] != "created":
            continue
        fields: dict[str, Any] = {}
        # The importer marks everything "imported"; put back how each recipe was made
        if entry.get("source_type") in _SOURCE_TYPES - {"imported"}:
            fields.update(source_type=entry["source_type"], imported_at=None)
        rating = entry.get("rating")
        if type(rating) is int and 1 <= rating <= 5:
            fields["rating"] = rating
        with contextlib.suppress(TypeError, ValueError):  # never cooked, or not a date
            fields["last_cooked_on"] = date.fromisoformat(entry.get("last_cooked_on"))
        if fields:
            restored[item["recipe_id"]] = fields
    if restored:
        rows = await db.execute(select(Recipe).where(Recipe.id.in_(restored)))
        for recipe in rows.scalars():
            for field, value in restored[recipe.id].items():
                setattr(recipe, field, value)
    return results, id_map


async def _restore_backup_extras(
    data: dict[str, Any], id_map: dict[int, int], user_id: int, household_id: int, db: AsyncSession
) -> dict[str, int]:
    """Add the backup's collections, meal plans and shopping lists that are missing."""
    counts = dict.fromkeys(
        (
            "collections",
            "collection_recipes",
            "meal_plans",
            "planned_meals",
            "planned_meals_skipped",
            "shopping_lists",
            "shopping_lists_skipped",
        ),
        0,
    )

    def new_id(old_id: Any) -> int | None:
        return id_map.get(old_id) if isinstance(old_id, int) else None

    # Collections match by name; recipes missing from one are added to it
    rows = await db.execute(
        select(Collection).where(Collection.user_id == user_id).order_by(Collection.id)
    )
    collections: dict[str, Collection] = {}
    for existing in rows.scalars():
        collections.setdefault(existing.name, existing)
    for entry in _dicts(data.get("collections")):
        name = _text(entry.get("name"), 100)
        if not name:
            continue
        collection = collections.get(name)
        if not collection:
            collection = Collection(
                user_id=user_id,
                household_id=household_id,
                name=name,
                description=_text(entry.get("description")),
                icon=_text(entry.get("icon"), 50),
                is_default=False,
            )
            db.add(collection)
            await db.flush()
            collections[name] = collection
            counts["collections"] += 1
        linked = set(
            (
                await db.execute(
                    select(RecipeCollection.recipe_id).where(
                        RecipeCollection.collection_id == collection.id
                    )
                )
            ).scalars()
        )
        recipe_ids = entry.get("recipe_ids")
        for old_id in recipe_ids if isinstance(recipe_ids, list) else []:
            recipe_id = new_id(old_id)
            if recipe_id and recipe_id not in linked:
                db.add(RecipeCollection(recipe_id=recipe_id, collection_id=collection.id))
                linked.add(recipe_id)
                counts["collection_recipes"] += 1

    # Meal plans match by week; a meal is added unless the same recipe is already in
    # that day and slot. A meal whose recipe is not in the file (another member's
    # recipe) cannot be restored.
    for entry in _dicts(data.get("meal_plans")):
        try:
            week = date.fromisoformat(entry.get("week_start_date"))
        except (TypeError, ValueError):
            continue
        plan = (
            await db.execute(
                select(MealPlan).where(
                    MealPlan.household_id == household_id, MealPlan.week_start_date == week
                )
            )
        ).scalar_one_or_none()
        planned: set[tuple[Any, ...]] = set()
        if plan:
            meal_rows = await db.execute(
                select(PlannedMeal).where(PlannedMeal.meal_plan_id == plan.id)
            )
            planned = {
                (m.day_of_week, m.meal_type, m.recipe_id or m.title) for m in meal_rows.scalars()
            }
        for meal in _dicts(entry.get("meals")):
            day, meal_type, servings = (
                meal.get("day_of_week"),
                meal.get("meal_type"),
                meal.get("servings"),
            )
            # A free-text meal ("Leftovers") has a title and no recipe
            title = _text(meal.get("title"), 200) if meal.get("recipe_id") is None else None
            recipe_id = new_id(meal.get("recipe_id"))
            what = recipe_id or title
            if (
                what is None
                or not (isinstance(day, int) and 0 <= day <= 6)
                or not (isinstance(meal_type, str) and meal_type in _MEAL_TYPES)
            ):
                counts["planned_meals_skipped"] += 1
                continue
            if (day, meal_type, what) in planned:
                continue
            if not plan:
                plan = MealPlan(
                    household_id=household_id, week_start_date=week, created_by_user_id=user_id
                )
                db.add(plan)
                await db.flush()
                counts["meal_plans"] += 1
            db.add(
                PlannedMeal(
                    meal_plan_id=plan.id,
                    recipe_id=recipe_id,
                    title=title,
                    created_by_user_id=user_id,
                    day_of_week=int(day),
                    meal_type=meal_type,
                    servings=servings if isinstance(servings, int) and servings >= 1 else None,
                    notes=_text(meal.get("notes")),
                )
            )
            planned.add((day, meal_type, what))
            counts["planned_meals"] += 1

    # Shopping lists match by name; one that exists is left alone, items included
    names = set(
        (
            await db.execute(
                select(ShoppingList.name).where(ShoppingList.household_id == household_id)
            )
        ).scalars()
    )
    for entry in _dicts(data.get("shopping_lists")):
        name = _text(entry.get("name"), 255)
        if not name:
            continue
        if name in names:
            counts["shopping_lists_skipped"] += 1
            continue
        shopping_list = ShoppingList(
            household_id=household_id,
            name=name,
            description=_text(entry.get("description")),
            status="archived" if entry.get("status") == "archived" else "active",
            created_by_user_id=user_id,
        )
        db.add(shopping_list)
        await db.flush()
        names.add(name)
        counts["shopping_lists"] += 1
        order = 0
        for item in _dicts(entry.get("items")):
            item_name = _text(item.get("item_name"), 255)
            if not item_name:
                continue
            order += 1
            db.add(
                ShoppingListItem(
                    list_id=shopping_list.id,
                    item_name=item_name,
                    quantity=_text(item.get("quantity"), 100),
                    unit=_text(item.get("unit"), 50),
                    category=_text(item.get("category"), 100),
                    notes=_text(item.get("notes")),
                    checked=item.get("checked") is True,
                    display_order=order,
                )
            )
    return counts


@router.post("/backup")
@limiter.limit("100/hour")
async def restore_backup(
    request: Request,
    file: UploadFile = File(...),
    scope: Literal["recipes", "everything"] = Form("everything"),
    current_user: User = Depends(get_current_user),
    household: "Household" = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a Complete Backup file made by `GET /export/all`.

    Adds what is missing and skips what matches; nothing existing is changed or
    removed. `scope=recipes` restores only the recipes (with their notes);
    `scope=everything` also restores collections, meal plans and shopping lists.

    Returns the recipe results in the same shape as `POST /import/recipes`, plus
    `restored`: counts for the other sections (null for `scope=recipes`).
    """
    await validate_file_size(file)
    try:
        data = json.loads(await file.read())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise InvalidInputError("Invalid JSON file") from e
    if not (
        isinstance(data, dict)
        and data.get("export_type") == "complete_backup"
        and isinstance(data.get("recipes"), list)
    ):
        raise InvalidInputError("This file is not a Complete Backup from this application")

    # Read before any flush can expire the loaded objects
    user_id, household_id = current_user.id, household.id
    results, id_map = await _restore_backup_recipes(data["recipes"], user_id, household_id, db)
    restored = (
        await _restore_backup_extras(data, id_map, user_id, household_id, db)
        if scope == "everything"
        else None
    )
    await _commit_import_results(db)
    logger.info(
        "backup_restored",
        user_id=user_id,
        scope=scope,
        created=results["created"],
        skipped=results["skipped"],
        failed=results["failed"],
    )

    return {
        "success": True,
        "message": (
            f"Restored {results['created']} recipes, skipped {results['skipped']} "
            f"already here, failed {results['failed']}"
        ),
        "details": results,
        "restored": restored,
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
