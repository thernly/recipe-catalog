"""
Shopping List API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

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
    query = select(ShoppingList).where(ShoppingList.household_id == household.id)

    if status_filter:
        query = query.where(ShoppingList.status == status_filter)

    query = query.order_by(ShoppingList.created_at.desc())

    result = await db.execute(query)
    shopping_lists = result.scalars().all()

    # Get item counts for each list
    summaries = []
    for shopping_list in shopping_lists:
        count_result = await db.execute(
            select(func.count(ShoppingListItem.id)).where(
                ShoppingListItem.list_id == shopping_list.id
            )
        )
        item_count = count_result.scalar() or 0

        checked_count_result = await db.execute(
            select(func.count(ShoppingListItem.id)).where(
                and_(
                    ShoppingListItem.list_id == shopping_list.id,
                    ShoppingListItem.checked == True,
                )
            )
        )
        checked_count = checked_count_result.scalar() or 0

        summaries.append(
            ShoppingListSummary(
                id=shopping_list.id,
                household_id=shopping_list.household_id,
                name=shopping_list.name,
                description=shopping_list.description,
                status=shopping_list.status,
                created_at=shopping_list.created_at,
                item_count=item_count,
                checked_count=checked_count,
            )
        )

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
        select(ShoppingList).where(
            and_(ShoppingList.id == list_id, ShoppingList.household_id == household.id)
        )
    )
    shopping_list = result.scalar_one_or_none()

    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found"
        )

    # Load items
    items_result = await db.execute(
        select(ShoppingListItem)
        .where(ShoppingListItem.list_id == list_id)
        .order_by(ShoppingListItem.display_order, ShoppingListItem.created_at)
    )
    shopping_list.items = list(items_result.scalars().all())

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
    await db.refresh(shopping_list)

    # Load items
    items_result = await db.execute(
        select(ShoppingListItem)
        .where(ShoppingListItem.list_id == list_id)
        .order_by(ShoppingListItem.display_order, ShoppingListItem.created_at)
    )
    shopping_list.items = list(items_result.scalars().all())

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
    await db.refresh(shopping_list)

    # Load items
    items_result = await db.execute(
        select(ShoppingListItem)
        .where(ShoppingListItem.list_id == list_id)
        .order_by(ShoppingListItem.display_order, ShoppingListItem.created_at)
    )
    shopping_list.items = list(items_result.scalars().all())

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
    if recipe.ingredients:
        for idx, ingredient in enumerate(recipe.ingredients):
            # Simple parsing - just use the ingredient text as-is
            item = ShoppingListItem(
                list_id=shopping_list.id,
                item_name=ingredient,
                quantity=None,
                unit=None,
                category=None,
                notes=None,
                checked=False,
                display_order=idx,
            )
            db.add(item)

    await db.commit()
    await db.refresh(shopping_list)

    # Load items
    items_result = await db.execute(
        select(ShoppingListItem)
        .where(ShoppingListItem.list_id == shopping_list.id)
        .order_by(ShoppingListItem.display_order)
    )
    shopping_list.items = list(items_result.scalars().all())

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

    # Collect all ingredients from all recipes
    ingredients_list = []
    for planned_meal in planned_meals:
        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == planned_meal.recipe_id)
        )
        recipe = recipe_result.scalar_one_or_none()

        if recipe and recipe.ingredients:
            for ingredient in recipe.ingredients:
                ingredients_list.append(ingredient)

    # Add all ingredients as items (simple approach - no aggregation)
    for idx, ingredient in enumerate(ingredients_list):
        item = ShoppingListItem(
            list_id=shopping_list.id,
            item_name=ingredient,
            quantity=None,
            unit=None,
            category=None,
            notes=None,
            checked=False,
            display_order=idx,
        )
        db.add(item)

    await db.commit()
    await db.refresh(shopping_list)

    # Load items
    items_result = await db.execute(
        select(ShoppingListItem)
        .where(ShoppingListItem.list_id == shopping_list.id)
        .order_by(ShoppingListItem.display_order)
    )
    shopping_list.items = list(items_result.scalars().all())

    return shopping_list
