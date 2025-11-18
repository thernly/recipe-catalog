"""Tests for meal planning functionality."""

import pytest
import pytest_asyncio
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.household import Household
from app.models.meal_plan import MealPlan, PlannedMeal
from app.models.recipe import Recipe
from app.api.meal_plans import get_week_start


@pytest_asyncio.fixture
async def test_household(db: AsyncSession, test_user: User):
    """Create a test household."""
    household = Household(
        name="Test Household",
        owner_user_id=test_user.id,
        max_members=10,
    )
    db.add(household)
    await db.commit()
    await db.refresh(household)
    return household


@pytest_asyncio.fixture
async def test_recipe(db: AsyncSession, test_household: Household, test_user: User):
    """Create a test recipe."""
    recipe = Recipe(
        name="Test Recipe",
        description="A test recipe",
        recipe_data={
            "ingredients": ["1 cup flour", "2 eggs"],
            "instructions": ["Mix ingredients", "Cook"],
            "prep_time": 10,
            "cook_time": 20,
            "servings": 4,
        },
        household_id=test_household.id,
        user_id=test_user.id,
    )
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)
    return recipe


# ============================================
# Unit Tests for Helper Functions
# ============================================


def test_get_week_start_monday():
    """Test get_week_start with a Monday."""
    monday = date(2025, 1, 6)  # Monday
    result = get_week_start(monday)
    assert result == monday
    assert result.weekday() == 0


def test_get_week_start_wednesday():
    """Test get_week_start with a Wednesday."""
    wednesday = date(2025, 1, 8)  # Wednesday
    result = get_week_start(wednesday)
    assert result == date(2025, 1, 6)  # Previous Monday
    assert result.weekday() == 0


def test_get_week_start_sunday():
    """Test get_week_start with a Sunday."""
    sunday = date(2025, 1, 12)  # Sunday
    result = get_week_start(sunday)
    assert result == date(2025, 1, 6)  # Previous Monday
    assert result.weekday() == 0


# ============================================
# Integration Tests for Meal Plan CRUD
# ============================================


@pytest.mark.asyncio
async def test_create_meal_plan(
    db: AsyncSession, test_user: User, test_household: Household
):
    """Test creating a meal plan."""
    week_start = get_week_start(date.today())

    meal_plan = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )

    db.add(meal_plan)
    await db.commit()
    await db.refresh(meal_plan)

    assert meal_plan.id is not None
    assert meal_plan.household_id == test_household.id
    assert meal_plan.week_start_date == week_start
    assert meal_plan.created_by_user_id == test_user.id
    assert meal_plan.created_at is not None
    assert meal_plan.updated_at is not None


@pytest.mark.asyncio
async def test_unique_meal_plan_per_household_week(
    db: AsyncSession, test_user: User, test_household: Household
):
    """Test that only one meal plan can exist per household per week."""
    week_start = get_week_start(date.today())

    # Create first meal plan
    meal_plan1 = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    db.add(meal_plan1)
    await db.commit()

    # Attempt to create duplicate meal plan for same week
    meal_plan2 = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    db.add(meal_plan2)

    # Should raise integrity error
    with pytest.raises(Exception):
        await db.commit()


@pytest.mark.asyncio
async def test_get_meal_plan(
    db: AsyncSession, test_user: User, test_household: Household
):
    """Test retrieving a meal plan."""
    week_start = get_week_start(date.today())

    # Create meal plan
    meal_plan = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    db.add(meal_plan)
    await db.commit()
    await db.refresh(meal_plan)

    # Retrieve meal plan
    result = await db.execute(select(MealPlan).where(MealPlan.id == meal_plan.id))
    retrieved = result.scalar_one()

    assert retrieved.id == meal_plan.id
    assert retrieved.household_id == test_household.id


@pytest.mark.asyncio
async def test_delete_meal_plan(
    db: AsyncSession, test_user: User, test_household: Household
):
    """Test deleting a meal plan."""
    week_start = get_week_start(date.today())

    # Create meal plan
    meal_plan = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    db.add(meal_plan)
    await db.commit()
    await db.refresh(meal_plan)

    meal_plan_id = meal_plan.id

    # Delete meal plan
    await db.delete(meal_plan)
    await db.commit()

    # Verify deletion
    result = await db.execute(select(MealPlan).where(MealPlan.id == meal_plan_id))
    deleted = result.scalar_one_or_none()

    assert deleted is None


@pytest.mark.asyncio
async def test_list_meal_plans(
    db: AsyncSession, test_user: User, test_household: Household
):
    """Test listing meal plans for a household."""
    # Create multiple meal plans for different weeks
    week1 = get_week_start(date.today())
    week2 = week1 + timedelta(days=7)
    week3 = week1 - timedelta(days=7)

    for week in [week1, week2, week3]:
        meal_plan = MealPlan(
            household_id=test_household.id,
            week_start_date=week,
            created_by_user_id=test_user.id,
        )
        db.add(meal_plan)

    await db.commit()

    # Retrieve all meal plans for household
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.household_id == test_household.id)
        .order_by(MealPlan.week_start_date)
    )
    meal_plans = result.scalars().all()

    assert len(meal_plans) == 3
    # Verify chronological order
    assert meal_plans[0].week_start_date == week3
    assert meal_plans[1].week_start_date == week1
    assert meal_plans[2].week_start_date == week2


# ============================================
# Integration Tests for Planned Meal CRUD
# ============================================


@pytest.mark.asyncio
async def test_create_planned_meal(
    db: AsyncSession,
    test_user: User,
    test_household: Household,
    test_recipe: Recipe,
):
    """Test creating a planned meal."""
    # Create meal plan
    week_start = get_week_start(date.today())
    meal_plan = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    db.add(meal_plan)
    await db.commit()
    await db.refresh(meal_plan)

    # Create planned meal
    planned_meal = PlannedMeal(
        meal_plan_id=meal_plan.id,
        recipe_id=test_recipe.id,
        day_of_week=0,  # Monday
        meal_type="dinner",
        servings=4,
        notes="Test notes",
    )

    db.add(planned_meal)
    await db.commit()
    await db.refresh(planned_meal)

    assert planned_meal.id is not None
    assert planned_meal.meal_plan_id == meal_plan.id
    assert planned_meal.recipe_id == test_recipe.id
    assert planned_meal.day_of_week == 0
    assert planned_meal.meal_type == "dinner"
    assert planned_meal.servings == 4
    assert planned_meal.notes == "Test notes"


@pytest.mark.asyncio
async def test_update_planned_meal(
    db: AsyncSession,
    test_user: User,
    test_household: Household,
    test_recipe: Recipe,
):
    """Test updating a planned meal."""
    # Create meal plan and planned meal
    week_start = get_week_start(date.today())
    meal_plan = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    db.add(meal_plan)
    await db.commit()
    await db.refresh(meal_plan)

    planned_meal = PlannedMeal(
        meal_plan_id=meal_plan.id,
        recipe_id=test_recipe.id,
        day_of_week=0,
        meal_type="dinner",
        servings=4,
    )
    db.add(planned_meal)
    await db.commit()
    await db.refresh(planned_meal)

    # Update planned meal
    planned_meal.day_of_week = 2  # Wednesday
    planned_meal.meal_type = "lunch"
    planned_meal.servings = 6
    planned_meal.notes = "Updated notes"

    await db.commit()
    await db.refresh(planned_meal)

    assert planned_meal.day_of_week == 2
    assert planned_meal.meal_type == "lunch"
    assert planned_meal.servings == 6
    assert planned_meal.notes == "Updated notes"


@pytest.mark.asyncio
async def test_delete_planned_meal(
    db: AsyncSession,
    test_user: User,
    test_household: Household,
    test_recipe: Recipe,
):
    """Test deleting a planned meal."""
    # Create meal plan and planned meal
    week_start = get_week_start(date.today())
    meal_plan = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    db.add(meal_plan)
    await db.commit()
    await db.refresh(meal_plan)

    planned_meal = PlannedMeal(
        meal_plan_id=meal_plan.id,
        recipe_id=test_recipe.id,
        day_of_week=0,
        meal_type="dinner",
        servings=4,
    )
    db.add(planned_meal)
    await db.commit()
    await db.refresh(planned_meal)

    planned_meal_id = planned_meal.id

    # Delete planned meal
    await db.delete(planned_meal)
    await db.commit()

    # Verify deletion
    result = await db.execute(
        select(PlannedMeal).where(PlannedMeal.id == planned_meal_id)
    )
    deleted = result.scalar_one_or_none()

    assert deleted is None


@pytest.mark.asyncio
async def test_multiple_recipes_per_meal_slot(
    db: AsyncSession,
    test_user: User,
    test_household: Household,
):
    """Test adding multiple recipes to the same meal slot."""
    # Create two recipes
    recipe1 = Recipe(
        name="Recipe 1",
        description="First recipe",
        recipe_data={
            "ingredients": ["Ingredient 1"],
            "instructions": ["Instructions 1"],
            "prep_time": 10,
            "cook_time": 20,
            "servings": 4,
        },
        household_id=test_household.id,
        user_id=test_user.id,
    )
    recipe2 = Recipe(
        name="Recipe 2",
        description="Second recipe",
        recipe_data={
            "ingredients": ["Ingredient 2"],
            "instructions": ["Instructions 2"],
            "prep_time": 15,
            "cook_time": 25,
            "servings": 2,
        },
        household_id=test_household.id,
        user_id=test_user.id,
    )
    db.add(recipe1)
    db.add(recipe2)
    await db.commit()
    await db.refresh(recipe1)
    await db.refresh(recipe2)

    # Create meal plan
    week_start = get_week_start(date.today())
    meal_plan = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    db.add(meal_plan)
    await db.commit()
    await db.refresh(meal_plan)

    # Add both recipes to same day and meal type
    planned_meal1 = PlannedMeal(
        meal_plan_id=meal_plan.id,
        recipe_id=recipe1.id,
        day_of_week=0,  # Monday
        meal_type="dinner",
        servings=4,
    )
    planned_meal2 = PlannedMeal(
        meal_plan_id=meal_plan.id,
        recipe_id=recipe2.id,
        day_of_week=0,  # Monday
        meal_type="dinner",
        servings=2,
    )

    db.add(planned_meal1)
    db.add(planned_meal2)
    await db.commit()

    # Verify both meals exist for the same slot
    result = await db.execute(
        select(PlannedMeal).where(
            PlannedMeal.meal_plan_id == meal_plan.id,
            PlannedMeal.day_of_week == 0,
            PlannedMeal.meal_type == "dinner",
        )
    )
    meals = result.scalars().all()

    assert len(meals) == 2


@pytest.mark.asyncio
async def test_cascade_delete_planned_meals(
    db: AsyncSession,
    test_user: User,
    test_household: Household,
    test_recipe: Recipe,
):
    """Test that deleting a meal plan cascades to planned meals."""
    # Create meal plan with planned meals
    week_start = get_week_start(date.today())
    meal_plan = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    db.add(meal_plan)
    await db.commit()
    await db.refresh(meal_plan)

    # Add multiple planned meals
    for day in range(3):
        planned_meal = PlannedMeal(
            meal_plan_id=meal_plan.id,
            recipe_id=test_recipe.id,
            day_of_week=day,
            meal_type="dinner",
            servings=4,
        )
        db.add(planned_meal)

    await db.commit()

    # Verify planned meals exist
    result = await db.execute(
        select(PlannedMeal).where(PlannedMeal.meal_plan_id == meal_plan.id)
    )
    meals_before = result.scalars().all()
    assert len(meals_before) == 3

    # Delete meal plan
    await db.delete(meal_plan)
    await db.commit()

    # Verify planned meals are also deleted
    result = await db.execute(
        select(PlannedMeal).where(PlannedMeal.meal_plan_id == meal_plan.id)
    )
    meals_after = result.scalars().all()
    assert len(meals_after) == 0


# ============================================
# Tests for Household Scoping
# ============================================


@pytest.mark.asyncio
async def test_household_scoping(db: AsyncSession, test_user: User):
    """Test that meal plans are properly scoped to households."""
    # Create two households
    household1 = Household(
        name="Household 1",
        owner_user_id=test_user.id,
        max_members=10,
    )
    db.add(household1)
    await db.commit()
    await db.refresh(household1)

    # Create another user for household 2
    user2 = User(
        email="user2@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
    )
    db.add(user2)
    await db.commit()
    await db.refresh(user2)

    household2 = Household(
        name="Household 2",
        owner_user_id=user2.id,
        max_members=10,
    )
    db.add(household2)
    await db.commit()
    await db.refresh(household2)

    # Create meal plans for both households with same week
    week_start = get_week_start(date.today())

    meal_plan1 = MealPlan(
        household_id=household1.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    meal_plan2 = MealPlan(
        household_id=household2.id,
        week_start_date=week_start,
        created_by_user_id=user2.id,
    )

    db.add(meal_plan1)
    db.add(meal_plan2)
    await db.commit()

    # Verify each household has only its own meal plan
    result = await db.execute(
        select(MealPlan).where(MealPlan.household_id == household1.id)
    )
    household1_plans = result.scalars().all()
    assert len(household1_plans) == 1
    assert household1_plans[0].id == meal_plan1.id

    result = await db.execute(
        select(MealPlan).where(MealPlan.household_id == household2.id)
    )
    household2_plans = result.scalars().all()
    assert len(household2_plans) == 1
    assert household2_plans[0].id == meal_plan2.id


# ============================================
# Tests for Week Navigation
# ============================================


@pytest.mark.asyncio
async def test_week_navigation(
    db: AsyncSession, test_user: User, test_household: Household
):
    """Test navigating between different weeks."""
    today = date.today()
    current_week = get_week_start(today)
    next_week = current_week + timedelta(days=7)
    previous_week = current_week - timedelta(days=7)

    # Create meal plans for different weeks
    for week in [current_week, next_week, previous_week]:
        meal_plan = MealPlan(
            household_id=test_household.id,
            week_start_date=week,
            created_by_user_id=test_user.id,
        )
        db.add(meal_plan)

    await db.commit()

    # Test querying each week
    for week in [current_week, next_week, previous_week]:
        result = await db.execute(
            select(MealPlan).where(
                MealPlan.household_id == test_household.id,
                MealPlan.week_start_date == week,
            )
        )
        meal_plan = result.scalar_one_or_none()
        assert meal_plan is not None
        assert meal_plan.week_start_date == week


# ============================================
# Tests for Data Validation
# ============================================


@pytest.mark.asyncio
async def test_planned_meal_day_of_week_validation(
    db: AsyncSession,
    test_user: User,
    test_household: Household,
    test_recipe: Recipe,
):
    """Test that day_of_week is constrained to 0-6."""
    week_start = get_week_start(date.today())
    meal_plan = MealPlan(
        household_id=test_household.id,
        week_start_date=week_start,
        created_by_user_id=test_user.id,
    )
    db.add(meal_plan)
    await db.commit()
    await db.refresh(meal_plan)

    # Valid days (0-6) should work
    for day in range(7):
        planned_meal = PlannedMeal(
            meal_plan_id=meal_plan.id,
            recipe_id=test_recipe.id,
            day_of_week=day,
            meal_type="dinner",
            servings=4,
        )
        db.add(planned_meal)

    await db.commit()

    # Verify all 7 meals were created
    result = await db.execute(
        select(PlannedMeal).where(PlannedMeal.meal_plan_id == meal_plan.id)
    )
    meals = result.scalars().all()
    assert len(meals) == 7
