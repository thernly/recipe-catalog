"""
Shopping List API endpoints.
"""

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select, and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.core.exceptions import ShoppingListNotFoundError
from app.models.household import Household
from app.models.meal_plan import MealPlan, PlannedMeal
from app.models.recipe import Recipe
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.user import User
from app.schemas.shopping_list import (
    CategoryList,
    GenerateFromMealPlanRequest,
    GenerateFromRecipeRequest,
    ShoppingListCreate,
    ShoppingListItemCreate,
    ShoppingListItemUpdate,
    ShoppingListSummary,
    ShoppingListUpdate,
)
from app.schemas.shopping_list import (
    ShoppingList as ShoppingListSchema,
)
from app.schemas.shopping_list import (
    ShoppingListItem as ShoppingListItemSchema,
)
from app.services.aisles import DEFAULT_CATEGORIES
from app.services.ingredient_parser import (  # noqa: F401  (re-exported for callers and tests)
    consolidate_ingredients,
    format_quantity,
    get_base_ingredient_name,
    ingredient_key,
    normalize_unit,
    parse_ingredient_lines,
    parse_ingredient_string,
    parse_quantity,
    singularize_ingredient,
)
from app.services.recipe_cleanup import normalize_yield


router = APIRouter()

_ALTERNATIVES = re.compile(r"\s+(?:and/)?or\s+", re.IGNORECASE)

# Words that describe how an ingredient is sourced or kept, not a different ingredient:
# "homemade or store-bought chicken broth" is one item, "chicken broth".
# ponytail: fixed word list; extend it as new recipes turn up other pairs
_SOURCE_WORDS = {
    "homemade", "store-bought", "storebought", "fresh", "frozen", "canned", "dried",
    "jarred", "bottled", "boxed", "packaged", "thawed", "cooked", "uncooked", "raw",
    "salted", "unsalted", "sweetened", "unsweetened", "ripe", "leftover",
    # grind and size: "medium or fine cornmeal" is one item, "cornmeal"
    "fine", "medium", "coarse", "extra-fine", "large", "small",
}  # fmt: skip

# One-word ingredients that stand on their own and never borrow the next alternative's
# noun: "ghee or clarified butter" -> "ghee", not "ghee butter".
# ponytail: fixed word list; extend it as new recipes turn up other misses
_WHOLE_INGREDIENTS = {
    "ghee", "lard", "butter", "margarine", "shortening", "oil", "honey", "molasses",
    "water", "stock", "broth", "wine", "vinegar", "sugar", "salt", "pepper",
}  # fmt: skip

# "and" joins two items only between full names (or `_WHOLE_INGREDIENTS` words) on a
# line with no amount and no punctuation: "Kosher salt and black pepper", "Salt and
# pepper". Other one-word sides stay whole ("half and half", "sweet and sour sauce"),
# and so do prep notes, which carry an amount or punctuation ("2 potatoes peeled and
# cut", "butter, plus extra for the tin and to serve").
_AND = re.compile(r"\s+and\s+", re.IGNORECASE)
_TO_TASTE = re.compile(r"\s+to (taste|season)\b.*$", re.IGNORECASE)


def _split_items(name: str, has_quantity: bool) -> list[str]:
    """Split "A and B" into separate items (see `_AND`), then each "A or B"."""
    if not has_quantity:
        name = _TO_TASTE.sub("", name)
    parts = [p.strip() for p in _AND.split(name)]
    if (
        has_quantity
        or re.search(r"[\d(),;:]", name)
        or len(parts) < 2
        or any(" " not in p and p.lower() not in _WHOLE_INGREDIENTS for p in parts)
    ):
        parts = [name]
    return [alt for part in parts for alt in _split_alternatives(part)]


# Alternatives that name nothing to buy: "or a combination", "or both", "or any ..."
_VAGUE = re.compile(r"^(a combination|both|any\b|your favou?rite|another\b)", re.IGNORECASE)


def _split_alternatives(name: str) -> list[str]:
    """
    One shopping name per alternative in "A or B".

    - Full names split: "unsalted butter or olive oil" -> both.
    - A one-word alternative shares the last one's noun: "chicken or vegetable stock" ->
      "chicken stock", "vegetable stock"; "light or dark brown sugar" -> both sugars.
      Words in `_WHOLE_INGREDIENTS` don't: "ghee or clarified butter" -> "ghee",
      "clarified butter".
    - Source words collapse: "homemade or store-bought chicken broth" -> "chicken broth".
    - "or other neutral oil" lends its noun ("grapeseed oil") but is not an item itself;
      "or a combination" / "or both" are dropped.
    """
    parts = [p.strip() for p in _ALTERNATIVES.split(name)]
    parts = [p for p in parts if p and not _VAGUE.match(p)]
    if len(parts) < 2:
        return parts
    lefts, last = parts[:-1], parts[-1]
    last_words = last.split()

    if all(p.lower() in _SOURCE_WORDS for p in lefts):
        while len(last_words) > 1 and last_words[0].lower() in _SOURCE_WORDS:
            last_words.pop(0)
        return [" ".join(last_words)]

    is_other = last_words[0].lower() == "other"
    if is_other:
        last_words = last_words[1:]
    shared = " ".join(last_words[1:])  # the noun the one-word alternatives share

    names = []
    for part in lefts:
        if " " in part or not shared or part.lower() in _WHOLE_INGREDIENTS:
            names.append(part)
        elif part.lower() not in _SOURCE_WORDS:
            names.append(f"{part} {shared}")
    if not is_other:
        names.append(last)
    return names


def recipe_shopping_items(
    recipe_data: dict[str, Any], index: int | None = None
) -> list[dict[str, Any]]:
    """
    Shopping items for a recipe's ingredients (or only line `index`).

    Uses the stored `parsedIngredients`, parsing the raw lines for recipes saved before
    the parser existed. Recipe notes ("divided", "235ml") and trailing prep words
    ("finely chopped") are left off: they describe cooking, not shopping. A name with
    alternatives ("butter or olive oil") becomes one item per alternative, each with the
    line's amount. Ranges buy the upper bound.
    """
    entries = recipe_data.get("parsedIngredients")
    if not entries:
        lines = recipe_data.get("recipeIngredient") or recipe_data.get("ingredients") or []
        entries = [
            line if isinstance(line, dict) else parse_ingredient_lines([line])[0] for line in lines
        ]
    if index is not None:
        entries = entries[index : index + 1]

    items: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("header"):
            continue
        name = str(
            entry.get("item")
            or entry.get("name")
            or entry.get("ingredient")
            or entry.get("raw")
            or ""
        )
        quantity = _quantity_str(entry.get("quantityMax") or entry.get("quantity"))
        unit = entry.get("unit")
        for alternative in _split_items(name, quantity is not None):
            alt_quantity, alt_unit = quantity, unit
            if alternative[:1].isdigit() or alternative[:1] in "½¼¾⅓⅔⅛":
                # "1 tsp kosher salt or 1/2 tsp coarse salt": each side has its own amount
                parsed = parse_ingredient_lines([alternative])[0]
                if parsed.get("item"):
                    alternative = parsed["item"]
                    alt_quantity = _quantity_str(
                        parsed.get("quantityMax") or parsed.get("quantity")
                    )
                    alt_unit = parsed.get("unit")
            item_name = get_base_ingredient_name(alternative)
            if item_name:
                items.append(
                    {"item_name": item_name[:255], "quantity": alt_quantity, "unit": alt_unit}
                )
    return items


# A yield counted in servings: "4", "4 servings", "Serves 4", "4-6 servings" (the lower
# bound, so a range never under-buys). "1 loaf" and "12 cookies" do not match.
_SERVINGS_YIELD = re.compile(
    r"^\s*(?:serves|servings:?)?\s*(\d+(?:\.\d+)?)(?:\s*(?:-|–|to)\s*\d+(?:\.\d+)?)?"
    r"\s*(?:servings?|portions?|people|persons?)?\s*$",
    re.IGNORECASE,
)


def servings_factor(recipe_data: dict[str, Any], servings: int | None) -> float:
    """
    How much to multiply a recipe's amounts by to make `servings` servings.

    1 (as written) when no servings are planned or the recipe's yield is not a number
    of servings.
    """
    if not servings:
        return 1.0
    match = _SERVINGS_YIELD.match(str(normalize_yield(recipe_data.get("recipeYield")) or ""))
    recipe_servings = float(match.group(1)) if match else 0.0
    return servings / recipe_servings if recipe_servings else 1.0


def _numeric(quantity: str | None) -> float | None:
    """A stored quantity as a number ("1 1/2" -> 1.5), or None when blank or not numeric."""
    return parse_quantity(quantity) or None


def _quantity_str(value: Any) -> str | None:
    """parsedIngredients store numbers; items store strings ("6", not "6.0")."""
    if isinstance(value, (int, float)):
        return format_quantity(float(value))
    return (str(value).strip() or None) if value else None


async def add_or_merge_item(
    db: AsyncSession,
    list_id: int,
    *,
    item_name: str,
    quantity: str | None = None,
    unit: str | None = None,
    category: str | None = None,
    notes: str | None = None,
) -> ShoppingListItem:
    """
    Add an item to a list, merging it into a matching unchecked item.

    Every add path calls this. Items match on `ingredient_key` (the singular base name
    `consolidate_ingredients` groups on). A blank amount ("salt, to taste") folds into
    any match; two amounts are summed when the units match and both are numeric,
    otherwise ("a pinch", cups vs grams) a separate item is added. Units are never
    converted. Distinct notes
    are joined with "; ". Checked items are never merged into.
    """
    unit = normalize_unit(unit)
    quantity = (quantity or "").strip() or None
    key = ingredient_key(item_name)
    # ponytail: one query per added item; batch-load if lists grow to hundreds of adds
    candidates = await db.execute(
        select(ShoppingListItem)
        .where(ShoppingListItem.list_id == list_id, ShoppingListItem.checked.is_(False))
        .order_by(ShoppingListItem.id)
    )
    for existing in candidates.scalars():
        if ingredient_key(existing.item_name) != key:
            continue
        old_quantity = (existing.quantity or "").strip() or None
        if not old_quantity or not quantity:
            # "salt, to taste" adds no amount: fold it into the same item either way
            if not old_quantity and quantity:
                existing.quantity, existing.unit = quantity, unit
        elif normalize_unit(existing.unit) != unit:
            continue
        else:
            old_value, new_value = _numeric(old_quantity), _numeric(quantity)
            if old_value is None or new_value is None:
                continue
            existing.quantity = format_quantity(old_value + new_value)
        if notes and notes not in (existing.notes or "").split("; "):
            existing.notes = f"{existing.notes}; {notes}" if existing.notes else notes
        existing.category = existing.category or category
        await db.flush()
        return existing

    max_order = (
        await db.execute(
            select(func.max(ShoppingListItem.display_order)).where(
                ShoppingListItem.list_id == list_id
            )
        )
    ).scalar() or 0
    item = ShoppingListItem(
        list_id=list_id,
        item_name=item_name,
        quantity=quantity,
        unit=unit,
        category=category,
        notes=notes,
        checked=False,
        display_order=max_order + 1,
    )
    db.add(item)
    await db.flush()
    return item


async def _household_list(db: AsyncSession, list_id: int, household_id: int) -> ShoppingList:
    """The list if it belongs to the household, else ShoppingListNotFoundError (404)."""
    result = await db.execute(
        select(ShoppingList).where(
            ShoppingList.id == list_id, ShoppingList.household_id == household_id
        )
    )
    shopping_list = result.unique().scalar_one_or_none()
    if not shopping_list:
        raise ShoppingListNotFoundError(list_id)
    return shopping_list


async def _load_with_items(db: AsyncSession, list_id: int) -> ShoppingList:
    result = await db.execute(
        select(ShoppingList)
        .where(ShoppingList.id == list_id)
        .options(selectinload(ShoppingList.items))
        .execution_options(populate_existing=True)
    )
    return result.unique().scalar_one()


@router.get("/categories", response_model=CategoryList)
async def get_categories():
    """
    Get default shopping list categories.

    Returns:
        CategoryList: List of default categories
    """
    return CategoryList(categories=DEFAULT_CATEGORIES)


@router.post("/", response_model=ShoppingListSchema, status_code=status.HTTP_201_CREATED)
async def create_shopping_list(
    shopping_list_data: ShoppingListCreate,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new shopping list.

    Args:
        shopping_list_data: Shopping list data
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        ShoppingList: The created shopping list
    """
    shopping_list = ShoppingList(
        household_id=household.id,
        name=shopping_list_data.name,
        description=shopping_list_data.description,
        status="active",
        created_by_user_id=current_user.id,
    )
    db.add(shopping_list)
    await db.commit()
    await db.refresh(shopping_list)

    # Reload shopping list with items eagerly loaded to avoid lazy loading issues
    result = await db.execute(
        select(ShoppingList)
        .where(ShoppingList.id == shopping_list.id)
        .options(selectinload(ShoppingList.items))
    )
    shopping_list = result.scalar_one()

    return shopping_list


@router.get("/", response_model=list[ShoppingListSummary])
async def list_shopping_lists(
    limit: int = 100,
    offset: int = 0,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    List all shopping lists for the user's household.

    Args:
        limit: Maximum number of shopping lists to return (default 100)
        offset: Number of shopping lists to skip (default 0)
        status_filter: Optional status filter (active/archived)
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        List[ShoppingListSummary]: List of shopping list summaries
    """
    # Use a single query with JOIN and aggregation to avoid N+1 queries
    query: Select[Any] = (
        select(
            ShoppingList.id,
            ShoppingList.household_id,
            ShoppingList.name,
            ShoppingList.description,
            ShoppingList.status,
            ShoppingList.created_by_user_id,
            User.display_name.label("created_by_name"),
            ShoppingList.created_at,
            func.count(ShoppingListItem.id).label("item_count"),
            func.sum(case((ShoppingListItem.checked, 1), else_=0)).label("checked_count"),
        )
        .outerjoin(ShoppingListItem, ShoppingList.id == ShoppingListItem.list_id)
        .outerjoin(User, User.id == ShoppingList.created_by_user_id)
        .where(ShoppingList.household_id == household.id)
        .group_by(
            ShoppingList.id,
            ShoppingList.household_id,
            ShoppingList.name,
            ShoppingList.description,
            ShoppingList.status,
            ShoppingList.created_by_user_id,
            User.display_name,
            ShoppingList.created_at,
        )
        .order_by(ShoppingList.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status_filter:
        query = query.where(ShoppingList.status == status_filter)

    result = await db.execute(query)
    rows = result.all()

    summaries = [
        ShoppingListSummary(
            id=row.id,
            household_id=row.household_id,
            name=row.name,
            description=row.description,
            status=row.status,
            created_by_user_id=row.created_by_user_id,
            created_by_name=row.created_by_name,
            created_at=row.created_at,
            item_count=row.item_count or 0,
            checked_count=row.checked_count or 0,
        )
        for row in rows
    ]

    return summaries


@router.get("/{list_id}", response_model=ShoppingListSchema)
async def get_shopping_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific shopping list with all items.

    Args:
        list_id: Shopping list ID
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        ShoppingList: The shopping list with all items
    """
    result = await db.execute(
        select(ShoppingList)
        .where(and_(ShoppingList.id == list_id, ShoppingList.household_id == household.id))
        .options(selectinload(ShoppingList.items))
    )
    shopping_list = result.scalar_one_or_none()

    if not shopping_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    return shopping_list


@router.patch("/{list_id}", response_model=ShoppingListSchema)
async def update_shopping_list(
    list_id: int,
    update_data: ShoppingListUpdate,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a shopping list.

    Args:
        list_id: Shopping list ID
        update_data: Update data
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        ShoppingList: The updated shopping list
    """
    result = await db.execute(
        select(ShoppingList).where(
            and_(ShoppingList.id == list_id, ShoppingList.household_id == household.id)
        )
    )
    shopping_list = result.scalar_one_or_none()

    if not shopping_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    # Update fields
    if update_data.name is not None:
        shopping_list.name = update_data.name
    if update_data.description is not None:
        shopping_list.description = update_data.description
    if update_data.status is not None:
        shopping_list.status = update_data.status

    await db.commit()

    # Reload shopping list with items eagerly loaded
    result = await db.execute(
        select(ShoppingList)
        .where(ShoppingList.id == list_id)
        .options(selectinload(ShoppingList.items))
    )
    shopping_list = result.scalar_one()

    return shopping_list


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a shopping list.

    Args:
        list_id: Shopping list ID
        current_user: The authenticated user
        household: The user's household
        db: Database session
    """
    result = await db.execute(
        select(ShoppingList).where(
            and_(ShoppingList.id == list_id, ShoppingList.household_id == household.id)
        )
    )
    shopping_list = result.scalar_one_or_none()

    if not shopping_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    await db.delete(shopping_list)
    await db.commit()


@router.post("/{list_id}/archive", response_model=ShoppingListSchema)
async def archive_shopping_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive a shopping list.

    Args:
        list_id: Shopping list ID
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        ShoppingList: The archived shopping list
    """
    result = await db.execute(
        select(ShoppingList).where(
            and_(ShoppingList.id == list_id, ShoppingList.household_id == household.id)
        )
    )
    shopping_list = result.scalar_one_or_none()

    if not shopping_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    shopping_list.status = "archived"
    await db.commit()

    # Reload shopping list with items eagerly loaded
    result = await db.execute(
        select(ShoppingList)
        .where(ShoppingList.id == list_id)
        .options(selectinload(ShoppingList.items))
    )
    shopping_list = result.scalar_one()

    return shopping_list


@router.post("/{list_id}/duplicate", response_model=ShoppingListSchema)
async def duplicate_shopping_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Duplicate a shopping list.

    Args:
        list_id: Shopping list ID to duplicate
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        ShoppingList: The new duplicated shopping list
    """
    result = await db.execute(
        select(ShoppingList).where(
            and_(ShoppingList.id == list_id, ShoppingList.household_id == household.id)
        )
    )
    original_list = result.scalar_one_or_none()

    if not original_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    # Create new list
    new_list = ShoppingList(
        household_id=household.id,
        name=f"{original_list.name} (Copy)",
        description=original_list.description,
        status="active",
        created_by_user_id=current_user.id,
    )
    db.add(new_list)
    await db.flush()

    # Copy items
    items_result = await db.execute(
        select(ShoppingListItem).where(ShoppingListItem.list_id == list_id)
    )
    original_items = items_result.scalars().all()

    for item in original_items:
        new_item = ShoppingListItem(
            list_id=new_list.id,
            item_name=item.item_name,
            quantity=item.quantity,
            unit=item.unit,
            category=item.category,
            notes=item.notes,
            checked=False,  # Reset checked status in copy
            display_order=item.display_order,
        )
        db.add(new_item)

    await db.commit()
    return await _load_with_items(db, new_list.id)


@router.post(
    "/{list_id}/items",
    response_model=ShoppingListItemSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_item_to_list(
    list_id: int,
    item_data: ShoppingListItemCreate,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Add an item to a shopping list, merged into a matching unchecked item if there is
    one (see `add_or_merge_item`). Returns the new or merged item.
    """
    await _household_list(db, list_id, household.id)
    item = await add_or_merge_item(
        db,
        list_id,
        item_name=item_data.item_name,
        quantity=item_data.quantity,
        unit=item_data.unit,
        category=item_data.category,
        notes=item_data.notes,
    )
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/items/{item_id}", response_model=ShoppingListItemSchema)
async def update_shopping_list_item(
    item_id: int,
    update_data: ShoppingListItemUpdate,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a shopping list item.

    Args:
        item_id: Item ID
        update_data: Update data
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        ShoppingListItem: The updated item
    """
    # Get item and verify it belongs to a list in the user's household
    result = await db.execute(
        select(ShoppingListItem)
        .join(ShoppingList)
        .where(
            and_(
                ShoppingListItem.id == item_id,
                ShoppingList.household_id == household.id,
            )
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # Update fields
    if update_data.item_name is not None:
        item.item_name = update_data.item_name
    if update_data.quantity is not None:
        item.quantity = update_data.quantity
    if update_data.unit is not None:
        item.unit = update_data.unit
    if update_data.category is not None:
        item.category = update_data.category
    if update_data.notes is not None:
        item.notes = update_data.notes
    if update_data.checked is not None:
        item.checked = update_data.checked
    if update_data.display_order is not None:
        item.display_order = update_data.display_order

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_list_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a shopping list item.

    Args:
        item_id: Item ID
        current_user: The authenticated user
        household: The user's household
        db: Database session
    """
    # Get item and verify it belongs to a list in the user's household
    result = await db.execute(
        select(ShoppingListItem)
        .join(ShoppingList)
        .where(
            and_(
                ShoppingListItem.id == item_id,
                ShoppingList.household_id == household.id,
            )
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    await db.delete(item)
    await db.commit()


@router.post("/from-recipe", response_model=ShoppingListSchema)
async def generate_from_recipe(
    request_data: GenerateFromRecipeRequest,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a shopping list from a recipe.

    Args:
        request_data: Request data with recipe ID and optional list name
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        ShoppingList: The created shopping list with items
    """
    # Get recipe
    result = await db.execute(
        select(Recipe).where(
            and_(
                Recipe.id == request_data.recipe_id,
                Recipe.deleted_at.is_(None),
                Recipe.household_id == household.id,
            )
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    if request_data.shopping_list_id is not None:
        shopping_list = await _household_list(db, request_data.shopping_list_id, household.id)
    else:
        shopping_list = ShoppingList(
            household_id=household.id,
            name=request_data.list_name or f"Shopping list for {recipe.name}",
            description=f"Generated from recipe: {recipe.name}",
            status="active",
            created_by_user_id=current_user.id,
        )
        db.add(shopping_list)
        await db.flush()

    # Add ingredients as items
    for fields in recipe_shopping_items(recipe.recipe_data or {}, request_data.ingredient_index):
        await add_or_merge_item(db, shopping_list.id, **fields)

    await db.commit()
    return await _load_with_items(db, shopping_list.id)


@router.post("/from-meal-plan", response_model=ShoppingListSchema)
async def generate_from_meal_plan(
    request_data: GenerateFromMealPlanRequest,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a shopping list from a meal plan.

    Args:
        request_data: Request data with meal plan ID and optional selected meals
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        ShoppingList: The created shopping list with aggregated items. A meal with
        planned servings has its amounts scaled from the recipe's yield (see
        `servings_factor`).
    """
    # Get meal plan
    result = await db.execute(
        select(MealPlan).where(
            and_(
                MealPlan.id == request_data.meal_plan_id,
                MealPlan.household_id == household.id,
            )
        )
    )
    meal_plan = result.scalar_one_or_none()

    if not meal_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found")

    # Get planned meals
    query = select(PlannedMeal).where(PlannedMeal.meal_plan_id == meal_plan.id)

    if request_data.selected_meal_ids:
        query = query.where(PlannedMeal.id.in_(request_data.selected_meal_ids))

    planned_meals_result = await db.execute(query)
    planned_meals = planned_meals_result.scalars().all()

    if not planned_meals:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No meals selected")

    if request_data.shopping_list_id is not None:
        shopping_list = await _household_list(db, request_data.shopping_list_id, household.id)
    else:
        week = meal_plan.week_start_date
        shopping_list = ShoppingList(
            household_id=household.id,
            name=request_data.list_name or f"Shopping list for week of {week}",
            description=f"Generated from meal plan for week of {week}",
            status="active",
            created_by_user_id=current_user.id,
        )
        db.add(shopping_list)
        await db.flush()

    # Collect all ingredients from all recipes as structured data
    ingredients_data: list[dict[str, Any]] = []
    recipe_result = await db.execute(
        select(Recipe).where(
            Recipe.id.in_([meal.recipe_id for meal in planned_meals]),
            Recipe.household_id == household.id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipes_by_id = {recipe.id: recipe for recipe in recipe_result.scalars()}
    for planned_meal in planned_meals:
        recipe = recipes_by_id.get(planned_meal.recipe_id)

        if recipe and recipe.recipe_data:
            factor = servings_factor(recipe.recipe_data, planned_meal.servings)
            for item in recipe_shopping_items(recipe.recipe_data):
                # Amounts that are not numbers ("a pinch") cannot be scaled
                amount = _numeric(item["quantity"])
                ingredients_data.append(
                    {
                        "name": item["item_name"],
                        "quantity": amount * factor if amount else item["quantity"],
                        "unit": item["unit"],
                    }
                )

    # Consolidate ingredients by name and unit, summing quantities
    consolidated_ingredients = consolidate_ingredients(ingredients_data)

    for ingredient in consolidated_ingredients:
        await add_or_merge_item(
            db,
            shopping_list.id,
            item_name=str(ingredient["name"])[:255],
            quantity=ingredient["quantity"],
            unit=ingredient["unit"],
        )

    await db.commit()
    return await _load_with_items(db, shopping_list.id)
