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

    # Find eggs in consolidated list (now singularized to "egg")
    eggs = next(item for item in consolidated if item["name"].lower() == "egg")
    assert eggs["quantity"] == "5"
    assert eggs["unit"] is None


def test_ingredient_preparation_method_consolidation():
    """Test that ingredients with different preparation methods are consolidated."""
    from app.api.shopping_lists import (
        get_base_ingredient_name,
        consolidate_ingredients,
    )

    # Test get_base_ingredient_name helper
    assert get_base_ingredient_name("garlic (minced)") == "garlic"
    assert get_base_ingredient_name("garlic (chopped)") == "garlic"
    assert get_base_ingredient_name("garlic cloves") == "garlic"
    assert get_base_ingredient_name("garlic, minced") == "garlic"
    assert get_base_ingredient_name("onion (diced)") == "onion"
    assert get_base_ingredient_name("butter (melted)") == "butter"
    assert get_base_ingredient_name("carrots, sliced") == "carrots"
    assert get_base_ingredient_name("ginger minced") == "ginger"
    assert get_base_ingredient_name("tomatoes chopped") == "tomatoes"

    # Test consolidation with different preparation methods
    ingredients = [
        {"name": "garlic cloves", "quantity": "3", "unit": None},
        {"name": "garlic (minced)", "quantity": "2", "unit": None},
        {"name": "garlic (chopped)", "quantity": "1", "unit": None},
        {"name": "onion (diced)", "quantity": "1", "unit": None},
        {"name": "onion, sliced", "quantity": "1", "unit": None},
        {"name": "butter (melted)", "quantity": "1", "unit": "stick"},
        {"name": "butter", "quantity": "2", "unit": "stick"},
    ]

    consolidated = consolidate_ingredients(ingredients)

    # Should consolidate to 3 unique items (garlic, onion, butter)
    assert len(consolidated) == 3

    # Find garlic - all three variations should be combined
    garlic = next(item for item in consolidated if "garlic" in item["name"].lower())
    assert garlic["quantity"] == "6"
    assert garlic["name"].lower() == "garlic"  # Should use base name
    assert garlic["unit"] is None

    # Find onion - both variations should be combined
    onion = next(item for item in consolidated if "onion" in item["name"].lower())
    assert onion["quantity"] == "2"
    assert onion["name"].lower() == "onion"  # Should use base name
    assert onion["unit"] is None

    # Find butter - both variations should be combined
    butter = next(item for item in consolidated if "butter" in item["name"].lower())
    assert butter["quantity"] == "3"
    assert butter["name"].lower() == "butter"  # Should use base name
    assert butter["unit"] == "stick"


def test_section_headers_filtered_out():
    """Test that section headers (items ending with ':') are filtered out."""
    from app.api.shopping_lists import consolidate_ingredients

    ingredients = [
        {"name": "Pie Crust:", "quantity": None, "unit": None},
        {"name": "filling:", "quantity": None, "unit": None},
        {"name": "For the crust:", "quantity": None, "unit": None},
        {"name": "1 cup flour", "quantity": "1", "unit": "cup"},
        {"name": "2 eggs", "quantity": "2", "unit": None},
    ]

    # Parse the string-based ingredients
    from app.api.shopping_lists import parse_ingredient_string
    ingredients_data = []
    for ing in ingredients:
        if ing["quantity"] is None and ing["unit"] is None:
            # Already parsed
            ingredients_data.append(ing)
        else:
            # Parse string format
            qty, unit, name = parse_ingredient_string(f"{ing['quantity']} {ing['unit']} {ing['name']}" if ing['unit'] else f"{ing['quantity']} {ing['name']}")
            ingredients_data.append({"quantity": qty, "unit": unit, "name": name})

    consolidated = consolidate_ingredients(ingredients_data)

    # Section headers should be filtered out
    names = [item["name"] for item in consolidated]
    assert "pie crust:" not in [n.lower() for n in names]
    assert "filling:" not in [n.lower() for n in names]
    assert "for the crust:" not in [n.lower() for n in names]

    # Only flour and eggs should remain
    assert len(consolidated) == 2
    assert any("flour" in item["name"].lower() for item in consolidated)
    assert any("egg" in item["name"].lower() for item in consolidated)


def test_plural_consolidation():
    """Test that plural and singular forms are consolidated."""
    from app.api.shopping_lists import (
        singularize_ingredient,
        consolidate_ingredients,
    )

    # Test singularize_ingredient helper
    assert singularize_ingredient("onions") == "onion"
    assert singularize_ingredient("Onions") == "Onion"
    assert singularize_ingredient("tomatoes") == "tomato"
    assert singularize_ingredient("potatoes") == "potato"
    assert singularize_ingredient("carrots") == "carrot"
    assert singularize_ingredient("olives") == "olive"
    assert singularize_ingredient("berries") == "berry"

    # Test consolidation with plurals and case variations
    ingredients = [
        {"name": "onion (diced)", "quantity": "1", "unit": None},
        {"name": "onion, chopped", "quantity": "1", "unit": None},
        {"name": "Onions (sliced)", "quantity": "2", "unit": None},
        {"name": "Tomatoes", "quantity": "3", "unit": None},
        {"name": "tomato", "quantity": "1", "unit": None},
    ]

    consolidated = consolidate_ingredients(ingredients)

    # Should consolidate to 2 unique items (onion, tomato)
    assert len(consolidated) == 2

    # Find onion - all three variations should be combined
    onion = next(item for item in consolidated if "onion" in item["name"].lower())
    assert onion["quantity"] == "4"  # 1 + 1 + 2
    assert onion["name"].lower() == "onion"  # Should use singular form
    assert onion["unit"] is None

    # Find tomato - both variations should be combined
    tomato = next(item for item in consolidated if "tomato" in item["name"].lower())
    assert tomato["quantity"] == "4"  # 3 + 1
    assert tomato["name"].lower() == "tomato"  # Should use singular form
    assert tomato["unit"] is None


def test_case_insensitive_consolidation():
    """Test that ingredients with different cases are consolidated."""
    from app.api.shopping_lists import consolidate_ingredients

    ingredients = [
        {"name": "Garlic", "quantity": "2", "unit": None},
        {"name": "garlic", "quantity": "1", "unit": None},
        {"name": "GARLIC", "quantity": "1", "unit": None},
    ]

    consolidated = consolidate_ingredients(ingredients)

    # Should consolidate to 1 item
    assert len(consolidated) == 1

    garlic = consolidated[0]
    assert garlic["quantity"] == "4"  # 2 + 1 + 1
    assert garlic["name"].lower() == "garlic"
    assert garlic["unit"] is None
