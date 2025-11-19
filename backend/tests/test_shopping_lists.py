"""Tests for shopping list functionality."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.household import Household
from app.models.recipe import Recipe
from app.models.shopping_list import ShoppingList, ShoppingListItem


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
            "ingredients": ["1 cup flour", "2 eggs", "1 cup milk"],
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


@pytest_asyncio.fixture
async def test_shopping_list(
    db: AsyncSession, test_user: User, test_household: Household
):
    """Create a test shopping list."""
    shopping_list = ShoppingList(
        household_id=test_household.id,
        name="Test Shopping List",
        description="A test list",
        status="active",
        created_by_user_id=test_user.id,
    )
    db.add(shopping_list)
    await db.commit()
    await db.refresh(shopping_list)
    return shopping_list


# ============================================
# Integration Tests for Shopping List CRUD
# ============================================


@pytest.mark.asyncio
async def test_create_shopping_list(
    db: AsyncSession, test_user: User, test_household: Household
):
    """Test creating a shopping list."""
    shopping_list = ShoppingList(
        household_id=test_household.id,
        name="Weekly Groceries",
        description="Shopping for the week",
        status="active",
        created_by_user_id=test_user.id,
    )

    db.add(shopping_list)
    await db.commit()
    await db.refresh(shopping_list)

    assert shopping_list.id is not None
    assert shopping_list.name == "Weekly Groceries"
    assert shopping_list.status == "active"
    assert shopping_list.household_id == test_household.id


@pytest.mark.asyncio
async def test_create_shopping_list_item(
    db: AsyncSession, test_shopping_list: ShoppingList
):
    """Test creating a shopping list item."""
    item = ShoppingListItem(
        list_id=test_shopping_list.id,
        item_name="Milk",
        quantity="1",
        unit="gallon",
        category="Dairy",
        checked=False,
        display_order=0,
    )

    db.add(item)
    await db.commit()
    await db.refresh(item)

    assert item.id is not None
    assert item.item_name == "Milk"
    assert item.quantity == "1"
    assert item.unit == "gallon"
    assert item.category == "Dairy"
    assert item.checked is False


@pytest.mark.asyncio
async def test_shopping_list_items_relationship(
    db: AsyncSession, test_shopping_list: ShoppingList
):
    """Test that shopping list items are accessible via relationship."""
    # Add some items
    items = [
        ShoppingListItem(
            list_id=test_shopping_list.id,
            item_name=f"Item {i}",
            checked=False,
            display_order=i,
        )
        for i in range(3)
    ]

    for item in items:
        db.add(item)
    await db.commit()

    # Refresh shopping list
    await db.refresh(test_shopping_list)

    # Check items via relationship
    result = await db.execute(
        select(ShoppingListItem).where(
            ShoppingListItem.list_id == test_shopping_list.id
        )
    )
    loaded_items = result.scalars().all()

    assert len(loaded_items) == 3
    assert all(item.list_id == test_shopping_list.id for item in loaded_items)


@pytest.mark.asyncio
async def test_toggle_item_checked(db: AsyncSession, test_shopping_list: ShoppingList):
    """Test toggling item checked status."""
    item = ShoppingListItem(
        list_id=test_shopping_list.id,
        item_name="Bread",
        checked=False,
        display_order=0,
    )

    db.add(item)
    await db.commit()
    await db.refresh(item)

    assert item.checked is False

    # Toggle checked
    item.checked = True
    await db.commit()
    await db.refresh(item)

    assert item.checked is True


@pytest.mark.asyncio
async def test_archive_shopping_list(
    db: AsyncSession, test_shopping_list: ShoppingList
):
    """Test archiving a shopping list."""
    assert test_shopping_list.status == "active"

    test_shopping_list.status = "archived"
    await db.commit()
    await db.refresh(test_shopping_list)

    assert test_shopping_list.status == "archived"


@pytest.mark.asyncio
async def test_delete_shopping_list_cascades_items(
    db: AsyncSession, test_shopping_list: ShoppingList
):
    """Test that deleting a list also deletes its items."""
    # Add items
    items = [
        ShoppingListItem(
            list_id=test_shopping_list.id,
            item_name=f"Item {i}",
            checked=False,
            display_order=i,
        )
        for i in range(3)
    ]

    for item in items:
        db.add(item)
    await db.commit()

    list_id = test_shopping_list.id

    # Delete the list
    await db.delete(test_shopping_list)
    await db.commit()

    # Verify items are also deleted
    result = await db.execute(
        select(ShoppingListItem).where(ShoppingListItem.list_id == list_id)
    )
    remaining_items = result.scalars().all()

    assert len(remaining_items) == 0


@pytest.mark.asyncio
async def test_household_scoping(
    db: AsyncSession, test_user: User, test_household: Household
):
    """Test that shopping lists are scoped to households."""
    # Create another household
    other_household = Household(
        name="Other Household",
        owner_user_id=test_user.id,
        max_members=10,
    )
    db.add(other_household)
    await db.commit()
    await db.refresh(other_household)

    # Create lists in both households
    list1 = ShoppingList(
        household_id=test_household.id,
        name="List 1",
        status="active",
        created_by_user_id=test_user.id,
    )
    list2 = ShoppingList(
        household_id=other_household.id,
        name="List 2",
        status="active",
        created_by_user_id=test_user.id,
    )

    db.add(list1)
    db.add(list2)
    await db.commit()

    # Query lists for first household
    result = await db.execute(
        select(ShoppingList).where(ShoppingList.household_id == test_household.id)
    )
    household_lists = result.scalars().all()

    assert len(household_lists) == 1
    assert household_lists[0].name == "List 1"


@pytest.mark.asyncio
async def test_generate_from_recipe(
    db: AsyncSession, test_user: User, test_household: Household, test_recipe: Recipe
):
    """Test generating a shopping list from a recipe."""
    shopping_list = ShoppingList(
        household_id=test_household.id,
        name=f"Shopping list for {test_recipe.name}",
        description=f"Generated from recipe: {test_recipe.name}",
        status="active",
        created_by_user_id=test_user.id,
    )
    db.add(shopping_list)
    await db.flush()

    # Add ingredients as items
    ingredients = test_recipe.recipe_data.get("ingredients", [])
    if ingredients:
        for idx, ingredient in enumerate(ingredients):
            item = ShoppingListItem(
                list_id=shopping_list.id,
                item_name=ingredient,
                checked=False,
                display_order=idx,
            )
            db.add(item)

    await db.commit()
    await db.refresh(shopping_list)

    # Verify items were created
    result = await db.execute(
        select(ShoppingListItem).where(ShoppingListItem.list_id == shopping_list.id)
    )
    items = result.scalars().all()

    assert len(items) == len(ingredients)
    assert items[0].item_name == "1 cup flour"
    assert items[1].item_name == "2 eggs"


@pytest.mark.asyncio
async def test_ingredient_consolidation():
    """Test the ingredient consolidation helper functions."""
    from app.api.shopping_lists import (
        parse_ingredient_string,
        parse_quantity,
        normalize_unit,
        consolidate_ingredients,
    )

    # Test parse_ingredient_string
    qty, unit, name = parse_ingredient_string("1 stick butter")
    assert qty == "1"
    assert unit == "stick"
    assert name == "butter"

    qty, unit, name = parse_ingredient_string("2 cups flour")
    assert qty == "2"
    assert unit == "cups"
    assert name == "flour"

    qty, unit, name = parse_ingredient_string("3 eggs")
    assert qty == "3"
    assert unit is None
    assert name == "eggs"

    qty, unit, name = parse_ingredient_string("1/2 teaspoon salt")
    assert qty == "1/2"
    assert unit == "teaspoon"
    assert name == "salt"

    # Test parse_quantity
    assert parse_quantity("1") == 1.0
    assert parse_quantity("1.5") == 1.5
    assert parse_quantity("1/2") == 0.5
    assert parse_quantity("1/4") == 0.25
    assert parse_quantity("1 1/2") == 1.5
    assert parse_quantity("2-3") == 3.0  # Takes max of range

    # Test normalize_unit
    assert normalize_unit("sticks") == "stick"
    assert normalize_unit("cups") == "cup"
    assert normalize_unit("tbsp") == "tablespoon"
    assert normalize_unit("tsp") == "teaspoon"
    assert normalize_unit("oz") == "ounce"

    # Test consolidate_ingredients - the main feature
    ingredients = [
        {"name": "butter", "quantity": "1", "unit": "stick"},
        {"name": "butter", "quantity": "1", "unit": "stick"},
        {"name": "butter", "quantity": "1", "unit": "stick"},
        {"name": "flour", "quantity": "2", "unit": "cup"},
        {"name": "flour", "quantity": "1", "unit": "cup"},
        {"name": "eggs", "quantity": "3", "unit": None},
        {"name": "eggs", "quantity": "2", "unit": None},
    ]

    consolidated = consolidate_ingredients(ingredients)

    # Should consolidate to 3 unique items
    assert len(consolidated) == 3

    # Find butter in consolidated list
    butter = next(item for item in consolidated if item["name"].lower() == "butter")
    assert butter["quantity"] == "3"
    assert butter["unit"] == "stick"

    # Find flour in consolidated list
    flour = next(item for item in consolidated if item["name"].lower() == "flour")
    assert flour["quantity"] == "3"
    assert flour["unit"] == "cup"

    # Find eggs in consolidated list
    eggs = next(item for item in consolidated if item["name"].lower() == "eggs")
    assert eggs["quantity"] == "5"
    assert eggs["unit"] is None
