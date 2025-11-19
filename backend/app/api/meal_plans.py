"""
Meal Planning API endpoints.
"""

from datetime import date, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.models.user import User
from app.models.household import Household
from app.models.meal_plan import MealPlan, PlannedMeal
from app.models.recipe import Recipe
from app.schemas.meal_plan import (
    MealPlan as MealPlanSchema,
    MealPlanSummary,
    PlannedMealCreate,
    PlannedMealUpdate,
    PlannedMeal as PlannedMealSchema,
)

router = APIRouter()


def get_week_start(input_date: date) -> date:
    """Get the Monday of the week containing the given date."""
    return input_date - timedelta(days=input_date.weekday())


def planned_meal_to_schema(planned_meal: PlannedMeal) -> PlannedMealSchema:
    """Convert PlannedMeal ORM object to schema with recipe_name populated."""
    return PlannedMealSchema(
        id=planned_meal.id,
        meal_plan_id=planned_meal.meal_plan_id,
        recipe_id=planned_meal.recipe_id,
        recipe_name=planned_meal.recipe.name if planned_meal.recipe else None,
        day_of_week=planned_meal.day_of_week,
        meal_type=planned_meal.meal_type,
        servings=planned_meal.servings,
        notes=planned_meal.notes,
        created_at=planned_meal.created_at,
        updated_at=planned_meal.updated_at,
    )


@router.get("/", response_model=List[MealPlanSummary])
async def list_meal_plans(
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    List all meal plans for the user's household.

    Args:
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        List[MealPlanSummary]: List of meal plan summaries
    """
    # Use a single query with JOIN and aggregation to avoid N+1 queries
    query = (
        select(
            MealPlan.id,
            MealPlan.household_id,
            MealPlan.week_start_date,
            MealPlan.created_at,
            func.count(PlannedMeal.id).label("meal_count"),
        )
        .outerjoin(PlannedMeal, MealPlan.id == PlannedMeal.meal_plan_id)
        .where(MealPlan.household_id == household.id)
        .group_by(
            MealPlan.id,
            MealPlan.household_id,
            MealPlan.week_start_date,
            MealPlan.created_at,
        )
        .order_by(MealPlan.week_start_date.desc())
    )

    result = await db.execute(query)
    rows = result.all()

    summaries = [
        MealPlanSummary(
            id=row.id,
            household_id=row.household_id,
            week_start_date=row.week_start_date,
            created_at=row.created_at,
            meal_count=row.meal_count or 0,
        )
        for row in rows
    ]

    return summaries


@router.get("/current", response_model=MealPlanSchema)
async def get_current_week_meal_plan(
    week_start: date = Query(
        None,
        description="Week start date (Monday). If not provided, uses current week.",
    ),
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Get or create meal plan for a specific week.

    Args:
        week_start: Week start date (Monday). Defaults to current week.
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        MealPlan: The meal plan for the specified week
    """
    # If no week_start provided, use current week
    if week_start is None:
        week_start = get_week_start(date.today())
    else:
        # Ensure the provided date is a Monday
        week_start = get_week_start(week_start)

    # Try to find existing meal plan with eager loading of planned meals and recipes
    result = await db.execute(
        select(MealPlan)
        .options(
            selectinload(MealPlan.planned_meals).joinedload(PlannedMeal.recipe)
        )
        .where(
            and_(
                MealPlan.household_id == household.id,
                MealPlan.week_start_date == week_start,
            )
        )
    )
    meal_plan = result.scalar_one_or_none()

    # Create if doesn't exist
    if not meal_plan:
        meal_plan = MealPlan(
            household_id=household.id,
            week_start_date=week_start,
            created_by_user_id=current_user.id,
        )
        db.add(meal_plan)
        await db.commit()
        await db.refresh(meal_plan)

        # Explicitly load planned_meals for new meal plan (will be empty)
        await db.refresh(meal_plan, ["planned_meals"])

    # Convert to schema with recipe names
    return MealPlanSchema(
        id=meal_plan.id,
        household_id=meal_plan.household_id,
        week_start_date=meal_plan.week_start_date,
        created_by_user_id=meal_plan.created_by_user_id,
        created_at=meal_plan.created_at,
        updated_at=meal_plan.updated_at,
        planned_meals=[planned_meal_to_schema(pm) for pm in meal_plan.planned_meals],
    )


@router.get("/{meal_plan_id}", response_model=MealPlanSchema)
async def get_meal_plan(
    meal_plan_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific meal plan by ID.

    Args:
        meal_plan_id: The meal plan ID
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        MealPlan: The meal plan
    """
    result = await db.execute(
        select(MealPlan)
        .options(
            selectinload(MealPlan.planned_meals).joinedload(PlannedMeal.recipe)
        )
        .where(
            and_(
                MealPlan.id == meal_plan_id,
                MealPlan.household_id == household.id,
            )
        )
    )
    meal_plan = result.scalar_one_or_none()

    if not meal_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found",
        )

    # Convert to schema with recipe names
    return MealPlanSchema(
        id=meal_plan.id,
        household_id=meal_plan.household_id,
        week_start_date=meal_plan.week_start_date,
        created_by_user_id=meal_plan.created_by_user_id,
        created_at=meal_plan.created_at,
        updated_at=meal_plan.updated_at,
        planned_meals=[planned_meal_to_schema(pm) for pm in meal_plan.planned_meals],
    )


@router.delete("/{meal_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(
    meal_plan_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a meal plan.

    Args:
        meal_plan_id: The meal plan ID
        current_user: The authenticated user
        household: The user's household
        db: Database session
    """
    result = await db.execute(
        select(MealPlan).where(
            and_(
                MealPlan.id == meal_plan_id,
                MealPlan.household_id == household.id,
            )
        )
    )
    meal_plan = result.scalar_one_or_none()

    if not meal_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found",
        )

    await db.delete(meal_plan)
    await db.commit()


@router.post(
    "/{meal_plan_id}/meals",
    response_model=PlannedMealSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_planned_meal(
    meal_plan_id: int,
    meal_data: PlannedMealCreate,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a meal to a meal plan.

    Args:
        meal_plan_id: The meal plan ID
        meal_data: The planned meal data
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        PlannedMeal: The created planned meal
    """
    # Verify meal plan exists and belongs to household
    result = await db.execute(
        select(MealPlan).where(
            and_(
                MealPlan.id == meal_plan_id,
                MealPlan.household_id == household.id,
            )
        )
    )
    meal_plan = result.scalar_one_or_none()

    if not meal_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found",
        )

    # Verify recipe exists and belongs to household
    result = await db.execute(
        select(Recipe).where(
            and_(
                Recipe.id == meal_data.recipe_id,
                Recipe.household_id == household.id,
                Recipe.deleted_at.is_(None),
            )
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    # Create planned meal
    planned_meal = PlannedMeal(
        meal_plan_id=meal_plan_id,
        recipe_id=meal_data.recipe_id,
        day_of_week=meal_data.day_of_week,
        meal_type=meal_data.meal_type,
        servings=meal_data.servings,
        notes=meal_data.notes,
    )

    db.add(planned_meal)
    await db.commit()
    await db.refresh(planned_meal)

    # Set recipe relationship for schema conversion
    planned_meal.recipe = recipe

    return planned_meal_to_schema(planned_meal)


@router.patch("/{planned_meal_id}", response_model=PlannedMealSchema)
async def update_planned_meal(
    planned_meal_id: int,
    meal_data: PlannedMealUpdate,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a planned meal.

    Args:
        planned_meal_id: The planned meal ID
        meal_data: The updated meal data
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        PlannedMeal: The updated planned meal
    """
    # Get planned meal and verify it belongs to household
    result = await db.execute(
        select(PlannedMeal)
        .join(MealPlan)
        .where(
            and_(
                PlannedMeal.id == planned_meal_id,
                MealPlan.household_id == household.id,
            )
        )
    )
    planned_meal = result.scalar_one_or_none()

    if not planned_meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned meal not found",
        )

    # Update fields
    if meal_data.recipe_id is not None:
        # Verify new recipe exists and belongs to household
        result = await db.execute(
            select(Recipe).where(
                and_(
                    Recipe.id == meal_data.recipe_id,
                    Recipe.household_id == household.id,
                    Recipe.deleted_at.is_(None),
                )
            )
        )
        recipe = result.scalar_one_or_none()
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )
        planned_meal.recipe_id = meal_data.recipe_id

    if meal_data.day_of_week is not None:
        planned_meal.day_of_week = meal_data.day_of_week

    if meal_data.meal_type is not None:
        planned_meal.meal_type = meal_data.meal_type

    if meal_data.servings is not None:
        planned_meal.servings = meal_data.servings

    if meal_data.notes is not None:
        planned_meal.notes = meal_data.notes

    await db.commit()
    await db.refresh(planned_meal)

    # Load recipe relationship for schema conversion
    await db.refresh(planned_meal, ["recipe"])

    return planned_meal_to_schema(planned_meal)


@router.delete("/meals/{planned_meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planned_meal(
    planned_meal_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a planned meal from a meal plan.

    Args:
        planned_meal_id: The planned meal ID
        current_user: The authenticated user
        household: The user's household
        db: Database session
    """
    # Get planned meal and verify it belongs to household
    result = await db.execute(
        select(PlannedMeal)
        .join(MealPlan)
        .where(
            and_(
                PlannedMeal.id == planned_meal_id,
                MealPlan.household_id == household.id,
            )
        )
    )
    planned_meal = result.scalar_one_or_none()

    if not planned_meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned meal not found",
        )

    await db.delete(planned_meal)
    await db.commit()
