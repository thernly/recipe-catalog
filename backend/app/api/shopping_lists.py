"""
Shopping List API endpoints.
"""

from typing import List, Optional, Dict, Tuple
import re
from fractions import Fraction
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.models.user import User
from app.models.household import Household
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.recipe import Recipe
from app.models.meal_plan import MealPlan, PlannedMeal
from app.schemas.shopping_list import (
    ShoppingListCreate,
    ShoppingListUpdate,
    ShoppingList as ShoppingListSchema,
    ShoppingListSummary,
    ShoppingListItemCreate,
    ShoppingListItemUpdate,
    ShoppingListItem as ShoppingListItemSchema,
    GenerateFromRecipeRequest,
    GenerateFromMealPlanRequest,
    CategoryList,
)

router = APIRouter()

# Default store categories
DEFAULT_CATEGORIES = [
    "Produce",
    "Dairy",
    "Meat",
    "Bakery",
    "Frozen",
    "Pantry",
    "Household",
    "Other",
]


def parse_quantity(quantity_str: str) -> float:
    """
    Parse a quantity string into a float.
    Handles fractions (1/2, 3/4), mixed numbers (1 1/2), decimals, and ranges (1-2).

    Args:
        quantity_str: String representation of quantity

    Returns:
        float: Parsed quantity value
    """
    if not quantity_str or not quantity_str.strip():
        return 0.0

    quantity_str = quantity_str.strip()

    # Handle ranges (e.g., "1-2" -> use the higher value)
    if '-' in quantity_str and not quantity_str.startswith('-'):
        parts = quantity_str.split('-')
        if len(parts) == 2:
            try:
                return max(float(Fraction(parts[0].strip())), float(Fraction(parts[1].strip())))
            except (ValueError, ZeroDivisionError):
                pass

    # Handle mixed numbers (e.g., "1 1/2")
    parts = quantity_str.split()
    if len(parts) == 2:
        try:
            whole = float(Fraction(parts[0]))
            fraction = float(Fraction(parts[1]))
            return whole + fraction
        except (ValueError, ZeroDivisionError):
            pass

    # Handle simple fractions and decimals
    try:
        return float(Fraction(quantity_str))
    except (ValueError, ZeroDivisionError):
        return 0.0


def parse_ingredient_string(ingredient_str: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Parse an ingredient string into quantity, unit, and name.

    Examples:
        "1 stick butter" -> ("1", "stick", "butter")
        "2 cups flour" -> ("2", "cups", "flour")
        "3 eggs" -> ("3", None, "eggs")
        "salt" -> (None, None, "salt")

    Args:
        ingredient_str: The ingredient string to parse

    Returns:
        Tuple of (quantity, unit, name)
    """
    ingredient_str = ingredient_str.strip()

    # Pattern to match quantity (including fractions) at the start
    # Matches: "1", "1.5", "1/2", "1 1/2", "1-2"
    quantity_pattern = r'^(\d+(?:\s+\d+)?(?:[\/\-\.]\d+)?)\s+'
    match = re.match(quantity_pattern, ingredient_str)

    if match:
        quantity = match.group(1).strip()
        remainder = ingredient_str[match.end():].strip()

        # Common units
        units = [
            'cup', 'cups', 'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 'tsp',
            'ounce', 'ounces', 'oz', 'pound', 'pounds', 'lb', 'lbs', 'gram', 'grams', 'g',
            'kilogram', 'kilograms', 'kg', 'milliliter', 'milliliters', 'ml', 'liter', 'liters', 'l',
            'stick', 'sticks', 'clove', 'cloves', 'can', 'cans', 'package', 'packages', 'pkg',
            'bunch', 'bunches', 'head', 'heads', 'piece', 'pieces', 'slice', 'slices',
            'pinch', 'dash', 'sprig', 'sprigs', 'whole', 'large', 'medium', 'small'
        ]

        # Check if the next word is a unit
        words = remainder.split(None, 1)
        if words and words[0].lower() in units:
            unit = words[0]
            name = words[1] if len(words) > 1 else ''
            return (quantity, unit, name)
        else:
            # No unit found, rest is the name
            return (quantity, None, remainder)
    else:
        # No quantity found
        return (None, None, ingredient_str)


def normalize_unit(unit: Optional[str]) -> Optional[str]:
    """
    Normalize unit names for better consolidation.

    Args:
        unit: The unit string to normalize

    Returns:
        Normalized unit string or None
    """
    if not unit:
        return None

    unit_lower = unit.lower().strip()

    # Map variations to standard forms
    unit_map = {
        'tbsp': 'tablespoon',
        'tablespoons': 'tablespoon',
        'tsp': 'teaspoon',
        'teaspoons': 'teaspoon',
        'cups': 'cup',
        'oz': 'ounce',
        'ounces': 'ounce',
        'lb': 'pound',
        'lbs': 'pound',
        'pounds': 'pound',
        'g': 'gram',
        'grams': 'gram',
        'kg': 'kilogram',
        'kilograms': 'kilogram',
        'ml': 'milliliter',
        'milliliters': 'milliliter',
        'l': 'liter',
        'liters': 'liter',
        'sticks': 'stick',
        'cloves': 'clove',
        'cans': 'can',
        'packages': 'package',
        'pkg': 'package',
        'bunches': 'bunch',
        'heads': 'head',
        'pieces': 'piece',
        'slices': 'slice',
        'sprigs': 'sprig',
    }

    return unit_map.get(unit_lower, unit_lower)


def consolidate_ingredients(ingredients_data: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    """
    Consolidate ingredients by name and unit, summing quantities.

    Args:
        ingredients_data: List of dicts with 'quantity', 'unit', 'name' keys

    Returns:
        List of consolidated ingredient dicts
    """
    # Group by (normalized_name, normalized_unit)
    consolidated: Dict[Tuple[str, Optional[str]], Dict] = {}

    for ing in ingredients_data:
        name = ing.get('name', '').strip().lower()
        if not name:
            continue

        unit = normalize_unit(ing.get('unit'))
        quantity_str = ing.get('quantity')

        # Parse quantity
        quantity_value = parse_quantity(quantity_str) if quantity_str else 0.0

        key = (name, unit)

        if key in consolidated:
            # Add to existing quantity
            consolidated[key]['quantity_value'] += quantity_value
        else:
            # New ingredient
            consolidated[key] = {
                'name': ing.get('name', '').strip(),  # Keep original casing for display
                'unit': unit,
                'quantity_value': quantity_value,
            }

    # Convert back to list with formatted quantities
    result = []
    for (name_key, unit_key), data in consolidated.items():
        qty_value = data['quantity_value']

        # Format quantity nicely
        if qty_value == 0:
            qty_str = None
        elif qty_value == int(qty_value):
            qty_str = str(int(qty_value))
        else:
            # Try to convert to fraction if it's close to a common fraction
            frac = Fraction(qty_value).limit_denominator(16)
            if abs(float(frac) - qty_value) < 0.01:
                if frac.numerator > frac.denominator:
                    whole = frac.numerator // frac.denominator
                    remainder = frac.numerator % frac.denominator
                    if remainder > 0:
                        qty_str = f"{whole} {remainder}/{frac.denominator}"
                    else:
                        qty_str = str(whole)
                else:
                    qty_str = f"{frac.numerator}/{frac.denominator}"
            else:
                qty_str = f"{qty_value:.2f}".rstrip('0').rstrip('.')

        result.append({
            'name': data['name'],
            'unit': data['unit'],
            'quantity': qty_str,
        })

    return result


@router.get("/categories", response_model=CategoryList)
async def get_categories():
    """
    Get default shopping list categories.

    Returns:
        CategoryList: List of default categories
    """
    return CategoryList(categories=DEFAULT_CATEGORIES)


@router.post(
    "/", response_model=ShoppingListSchema, status_code=status.HTTP_201_CREATED
)
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
    return shopping_list


@router.get("/", response_model=List[ShoppingListSummary])
async def list_shopping_lists(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    List all shopping lists for the user's household.

    Args:
        status_filter: Optional status filter (active/archived)
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        List[ShoppingListSummary]: List of shopping list summaries
    """
    # Use a single query with JOIN and aggregation to avoid N+1 queries
    query = (
        select(
            ShoppingList.id,
            ShoppingList.household_id,
            ShoppingList.name,
            ShoppingList.description,
            ShoppingList.status,
            ShoppingList.created_at,
            func.count(ShoppingListItem.id).label("item_count"),
            func.sum(case((ShoppingListItem.checked, 1), else_=0)).label(
                "checked_count"
            ),
        )
        .outerjoin(ShoppingListItem, ShoppingList.id == ShoppingListItem.list_id)
        .where(ShoppingList.household_id == household.id)
        .group_by(
            ShoppingList.id,
            ShoppingList.household_id,
            ShoppingList.name,
            ShoppingList.description,
            ShoppingList.status,
            ShoppingList.created_at,
        )
        .order_by(ShoppingList.created_at.desc())
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
        .where(
            and_(ShoppingList.id == list_id, ShoppingList.household_id == household.id)
        )
        .options(selectinload(ShoppingList.items))
    )
    shopping_list = result.scalar_one_or_none()

    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found"
        )

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
    await db.refresh(new_list)

    # Load items
    items_result = await db.execute(
        select(ShoppingListItem)
        .where(ShoppingListItem.list_id == new_list.id)
        .order_by(ShoppingListItem.display_order, ShoppingListItem.created_at)
    )
    new_list.items = list(items_result.scalars().all())

    return new_list


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
    Add an item to a shopping list.

    Args:
        list_id: Shopping list ID
        item_data: Item data
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        ShoppingListItem: The created item
    """
    # Verify list exists and belongs to household
    result = await db.execute(
        select(ShoppingList).where(
            and_(ShoppingList.id == list_id, ShoppingList.household_id == household.id)
        )
    )
    shopping_list = result.scalar_one_or_none()

    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found"
        )

    # Get max display order
    max_order_result = await db.execute(
        select(func.max(ShoppingListItem.display_order)).where(
            ShoppingListItem.list_id == list_id
        )
    )
    max_order = max_order_result.scalar() or 0

    item = ShoppingListItem(
        list_id=list_id,
        item_name=item_data.item_name,
        quantity=item_data.quantity,
        unit=item_data.unit,
        category=item_data.category,
        notes=item_data.notes,
        checked=False,
        display_order=max_order + 1,
    )
    db.add(item)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

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
                Recipe.household_id == household.id,
            )
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    # Create shopping list
    list_name = request_data.list_name or f"Shopping list for {recipe.name}"
    shopping_list = ShoppingList(
        household_id=household.id,
        name=list_name,
        description=f"Generated from recipe: {recipe.name}",
        status="active",
        created_by_user_id=current_user.id,
    )
    db.add(shopping_list)
    await db.flush()

    # Add ingredients as items
    if recipe.recipe_data:
        # Support both 'recipeIngredient' (Schema.org format from frontend)
        # and 'ingredients' (legacy/test format) for backward compatibility
        ingredients = recipe.recipe_data.get(
            "recipeIngredient", recipe.recipe_data.get("ingredients", [])
        )
        if isinstance(ingredients, list):
            for idx, ingredient in enumerate(ingredients):
                # Handle both string and dict ingredient formats
                if isinstance(ingredient, str):
                    item_name = ingredient
                elif isinstance(ingredient, dict):
                    # If ingredient is a dict, try to format it nicely
                    name = ingredient.get("name", ingredient.get("ingredient", ""))
                    quantity = ingredient.get("quantity", "")
                    unit = ingredient.get("unit", "")
                    if quantity and unit:
                        item_name = f"{quantity} {unit} {name}".strip()
                    elif name:
                        item_name = name
                    else:
                        continue
                else:
                    continue

                item = ShoppingListItem(
                    list_id=shopping_list.id,
                    item_name=item_name,
                    quantity=None,
                    unit=None,
                    category=None,
                    notes=None,
                    checked=False,
                    display_order=idx,
                )
                db.add(item)

    await db.commit()

    # Reload shopping list with items eagerly loaded
    result = await db.execute(
        select(ShoppingList)
        .where(ShoppingList.id == shopping_list.id)
        .options(selectinload(ShoppingList.items))
    )
    shopping_list = result.scalar_one()

    return shopping_list


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
        ShoppingList: The created shopping list with aggregated items
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found"
        )

    # Get planned meals
    query = select(PlannedMeal).where(PlannedMeal.meal_plan_id == meal_plan.id)

    if request_data.selected_meal_ids:
        query = query.where(PlannedMeal.id.in_(request_data.selected_meal_ids))

    planned_meals_result = await db.execute(query)
    planned_meals = planned_meals_result.scalars().all()

    if not planned_meals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No meals selected"
        )

    # Create shopping list
    list_name = (
        request_data.list_name
        or f"Shopping list for week of {meal_plan.week_start_date}"
    )
    shopping_list = ShoppingList(
        household_id=household.id,
        name=list_name,
        description=f"Generated from meal plan for week of {meal_plan.week_start_date}",
        status="active",
        created_by_user_id=current_user.id,
    )
    db.add(shopping_list)
    await db.flush()

    # Collect all ingredients from all recipes as structured data
    ingredients_data = []
    for planned_meal in planned_meals:
        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == planned_meal.recipe_id)
        )
        recipe = recipe_result.scalar_one_or_none()

        if recipe and recipe.recipe_data:
            # Support both 'recipeIngredient' (Schema.org format from frontend)
            # and 'ingredients' (legacy/test format) for backward compatibility
            ingredients = recipe.recipe_data.get(
                "recipeIngredient", recipe.recipe_data.get("ingredients", [])
            )
            if isinstance(ingredients, list):
                for ingredient in ingredients:
                    # Handle both string and dict ingredient formats
                    if isinstance(ingredient, str):
                        # Parse string format
                        quantity, unit, name = parse_ingredient_string(ingredient)
                        ingredients_data.append({
                            'quantity': quantity,
                            'unit': unit,
                            'name': name,
                        })
                    elif isinstance(ingredient, dict):
                        # Use dict format directly
                        name = ingredient.get("name", ingredient.get("ingredient", ""))
                        quantity = ingredient.get("quantity", "")
                        unit = ingredient.get("unit", "")
                        ingredients_data.append({
                            'quantity': quantity if quantity else None,
                            'unit': unit if unit else None,
                            'name': name,
                        })

    # Consolidate ingredients by name and unit, summing quantities
    consolidated_ingredients = consolidate_ingredients(ingredients_data)

    # Add consolidated ingredients as shopping list items
    for idx, ingredient in enumerate(consolidated_ingredients):
        item = ShoppingListItem(
            list_id=shopping_list.id,
            item_name=ingredient['name'],
            quantity=ingredient['quantity'],
            unit=ingredient['unit'],
            category=None,
            notes=None,
            checked=False,
            display_order=idx,
        )
        db.add(item)

    await db.commit()

    # Reload shopping list with items eagerly loaded
    result = await db.execute(
        select(ShoppingList)
        .where(ShoppingList.id == shopping_list.id)
        .options(selectinload(ShoppingList.items))
    )
    shopping_list = result.scalar_one()

    return shopping_list
