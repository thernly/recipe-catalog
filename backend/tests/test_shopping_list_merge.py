"""Merge-on-add, add-to-existing-list and "created by" for shopping lists."""

from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.shopping_lists import add_or_merge_item, recipe_shopping_items
from app.models.meal_plan import MealPlan, PlannedMeal
from app.models.recipe import Recipe
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.user import User


BASE = "/api/v1/shopping-lists"


@pytest_asyncio.fixture
async def shopping_list(db: AsyncSession, test_user: User, test_household: dict) -> ShoppingList:
    sl = ShoppingList(
        household_id=test_household["id"], name="Weekly", created_by_user_id=test_user.id
    )
    db.add(sl)
    await db.commit()
    return sl


@pytest_asyncio.fixture
async def recipe(db: AsyncSession, test_user: User, test_household: dict) -> Recipe:
    r = Recipe(
        name="Pancakes",
        recipe_data={
            "parsedIngredients": [
                {"raw": "For the batter:", "header": True, "group": "For the batter"},
                {
                    "raw": "2 cups flour, sifted",
                    "quantity": 2,
                    "quantityMax": None,
                    "unit": "cup",
                    "item": "flour",
                    "note": "sifted",
                },
                {
                    "raw": "1-2 eggs",
                    "quantity": 1,
                    "quantityMax": 2,
                    "unit": None,
                    "item": "eggs",
                    "note": None,
                },
                {"raw": "seeds from 1 pod", "parsedBy": None},
            ]
        },
        household_id=test_household["id"],
        user_id=test_user.id,
    )
    db.add(r)
    await db.commit()
    return r


async def _add(db, sl, name, quantity=None, unit=None, notes=None):
    item = await add_or_merge_item(
        db, sl.id, item_name=name, quantity=quantity, unit=unit, notes=notes
    )
    await db.commit()
    return item


async def _items(db, sl) -> list[ShoppingListItem]:
    await db.refresh(sl, ["items"])
    return sorted(sl.items, key=lambda i: i.id)


# --- add_or_merge_item ---------------------------------------------------------


async def test_merge_same_unit_sums(db, shopping_list):
    await _add(db, shopping_list, "flour", "2", "cup")
    merged = await _add(db, shopping_list, "flour", "4", "cups")
    items = await _items(db, shopping_list)
    assert len(items) == 1
    assert (merged.quantity, merged.unit) == ("6", "cup")


async def test_different_unit_adds_separate(db, shopping_list):
    await _add(db, shopping_list, "flour", "2", "cup")
    await _add(db, shopping_list, "flour", "100", "g")
    assert len(await _items(db, shopping_list)) == 2


@pytest.mark.parametrize(
    ("first", "second", "total"),
    [
        (("2", "tablespoon"), ("1", "tsp"), ("2 1/3", "tablespoon")),
        (("1", "cup"), ("2", "tablespoons"), ("1 1/8", "cup")),
        (("1/4", "cup"), ("1", "teaspoon"), ("4 1/3", "tablespoon")),
        (("1", "teaspoon"), ("1", "teaspoon"), ("2", "teaspoon")),  # same unit: not regrouped
        (("500", "g"), ("1", "kg"), ("1 1/2", "kilogram")),
        (("200", "g"), ("1", "kg"), ("1200", "gram")),  # no tidy fraction of a kilogram
        (("750", "ml"), ("1", "l"), ("1 3/4", "liter")),
        (("8", "oz"), ("1", "lb"), ("1 1/2", "pound")),
    ],
)
async def test_related_units_are_added_together(db, shopping_list, first, second, total):
    await _add(db, shopping_list, "sugar", *first)
    merged = await _add(db, shopping_list, "sugar", *second)
    assert len(await _items(db, shopping_list)) == 1
    assert (merged.quantity, merged.unit) == total


async def test_metric_and_us_measures_stay_separate(db, shopping_list):
    await _add(db, shopping_list, "milk", "1", "cup")
    await _add(db, shopping_list, "milk", "250", "ml")
    await _add(db, shopping_list, "milk", "8", "oz")
    assert len(await _items(db, shopping_list)) == 3


async def test_no_unit_on_either_side_merges(db, shopping_list):
    await _add(db, shopping_list, "egg", "2")
    merged = await _add(db, shopping_list, "egg", "3")
    assert merged.quantity == "5"
    assert len(await _items(db, shopping_list)) == 1


async def test_fractions(db, shopping_list):
    await _add(db, shopping_list, "sugar", "1/2", "cup")
    merged = await _add(db, shopping_list, "sugar", "1 1/2", "cup")
    assert merged.quantity == "2"
    merged = await _add(db, shopping_list, "sugar", "1/4", "cup")
    assert merged.quantity == "2 1/4"


async def test_non_numeric_quantity_adds_separate(db, shopping_list):
    await _add(db, shopping_list, "salt", "a pinch")
    await _add(db, shopping_list, "salt", "1", "teaspoon")
    await _add(db, shopping_list, "salt", "1")  # numeric, but existing is "a pinch"
    assert len(await _items(db, shopping_list)) == 3


async def test_blank_quantity_folds_into_any_match(db, shopping_list):
    await _add(db, shopping_list, "Kosher salt")
    await _add(db, shopping_list, "kosher salt", "1", "teaspoon")
    await _add(db, shopping_list, "kosher salt")
    await _add(db, shopping_list, "kosher salt", "1", "teaspoon")
    items = await _items(db, shopping_list)
    assert [(i.quantity, i.unit) for i in items] == [("2", "teaspoon")]


def test_leading_prep_words_dropped():
    lines = ["1/4 cup Chopped fresh flat-leaf parsley leaves", "1 cup finely chopped onion"]
    names = [i["item_name"] for i in recipe_shopping_items({"recipeIngredient": lines})]
    assert names == ["fresh flat-leaf parsley leaves", "onion"]


def test_alternatives_with_their_own_amounts():
    line = "1 teaspoon kosher salt (such as Diamond Crystal) or 1/2 teaspoon coarse kosher salt"
    items = recipe_shopping_items({"recipeIngredient": [line]})
    assert [(i["item_name"], i["quantity"], i["unit"]) for i in items] == [
        ("kosher salt", "1", "teaspoon"),
        ("coarse kosher salt", "1/2", "teaspoon"),
    ]


async def test_checked_item_is_not_merged_into(db, shopping_list):
    first = await _add(db, shopping_list, "milk", "1", "liter")
    first.checked = True
    await db.commit()
    second = await _add(db, shopping_list, "milk", "1", "liter")
    assert second.id != first.id
    assert first.quantity == "1"


async def test_plural_and_singular_names_merge(db, shopping_list):
    await _add(db, shopping_list, "Tomatoes", "2")
    merged = await _add(db, shopping_list, "tomato", "1")
    assert merged.item_name == "Tomatoes"
    assert merged.quantity == "3"


async def test_distinct_notes_are_joined(db, shopping_list):
    await _add(db, shopping_list, "onion", "1", notes="diced")
    await _add(db, shopping_list, "onions", "1", notes="diced")
    merged = await _add(db, shopping_list, "onion", "1", notes="sliced")
    assert merged.notes == "diced; sliced"
    assert merged.quantity == "3"
    # A note that is itself several notes adds only the new ones
    merged = await _add(db, shopping_list, "onion", "1", notes="sliced; for Soup")
    assert merged.notes == "diced; sliced; for Soup"


# --- API -------------------------------------------------------------------------


async def test_manual_add_merges(client: AsyncClient, auth_headers, shopping_list):
    url = f"{BASE}/{shopping_list.id}/items"
    first = await client.post(
        url, json={"item_name": "flour", "quantity": "2", "unit": "cup"}, headers=auth_headers
    )
    second = await client.post(
        url, json={"item_name": "Flour", "quantity": "4", "unit": "cups"}, headers=auth_headers
    )
    assert first.status_code == second.status_code == 201
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["quantity"] == "6"


async def test_from_recipe_uses_parsed_fields(client: AsyncClient, auth_headers, recipe):
    res = await client.post(
        f"{BASE}/from-recipe", json={"recipe_id": recipe.id}, headers=auth_headers
    )
    assert res.status_code == 200
    items = {i["item_name"]: i for i in res.json()["items"]}
    assert set(items) == {"flour", "eggs", "seeds from 1 pod"}
    assert (items["flour"]["quantity"], items["flour"]["unit"]) == ("2", "cup")
    # Only the recipe's name: prep notes ("sifted") stay off the list
    assert items["flour"]["notes"] == "for Pancakes"
    assert items["eggs"]["quantity"] == "2"  # upper bound of the range
    assert items["seeds from 1 pod"]["quantity"] is None


def test_recipe_items_drop_prep_and_metric_notes_for_unparsed_recipes():
    # A recipe saved before parsedIngredients existed: raw lines only
    data = {
        "recipeIngredient": [
            "1 cup (235ml) whole milk",
            "6 ounces (170g) grated Gruyere cheese, divided",
            "1 onion, finely chopped",
            "2 eggs, beaten",
        ]
    }
    items = recipe_shopping_items(data)
    assert [(i["item_name"], i["quantity"], i["unit"]) for i in items] == [
        ("whole milk", "1", "cup"),
        ("grated Gruyere cheese", "6", "ounce"),
        ("onion", "1", None),
        ("eggs", "2", None),
    ]
    assert all("notes" not in i for i in items)


def test_recipe_items_split_alternatives():
    data = {"recipeIngredient": ["2 tablespoons unsalted butter or olive oil"]}
    assert [(i["item_name"], i["quantity"]) for i in recipe_shopping_items(data)] == [
        ("unsalted butter", "2"),
        ("olive oil", "2"),
    ]


def test_source_word_alternatives_are_one_item():
    lines = [
        "4 cups homemade or store-bought low-sodium chicken broth",
        "1 cup fresh or frozen peas",
        "2 tablespoons salted or unsalted butter",
    ]
    names = [i["item_name"] for i in recipe_shopping_items({"recipeIngredient": lines})]
    assert names == ["low-sodium chicken broth", "peas", "butter"]


def test_one_word_alternatives_share_the_noun():
    lines = [
        "2 cups chicken or vegetable stock",
        "1/4 cup light or dark brown sugar",
        "1/4 cup grapeseed or other neutral oil",
        "1 tablespoon sesame or poppy seeds or a combination (optional)",
        "1 cup pecans or walnuts",
    ]
    names = [i["item_name"] for i in recipe_shopping_items({"recipeIngredient": lines})]
    assert names == [
        "chicken stock",
        "vegetable stock",
        "light brown sugar",
        "dark brown sugar",
        "grapeseed oil",
        "sesame seeds",
        "poppy seeds",
        "pecans",
        "walnuts",
    ]


def test_name_heuristic_misses():
    lines = [
        "2 tablespoons ghee or clarified butter",
        "1 cup medium or fine cornmeal",
        "Kosher salt and black pepper",
        "1 cup half and half",
        "2 tablespoons sweet and sour sauce",
        "4 ounces milk or dark chocolate",
        "Kosher salt and black or white pepper",
        "2 potatoes peeled and cut into cubes",
        "For serving: chopped walnuts and extra honey",
        "Salt and pepper to season",
    ]
    names = [i["item_name"] for i in recipe_shopping_items({"recipeIngredient": lines})]
    assert names == [
        "ghee",
        "clarified butter",
        "cornmeal",
        "Kosher salt",
        "black pepper",
        "half and half",
        "sweet and sour sauce",
        "milk chocolate",
        "dark chocolate",
        "Kosher salt",
        "black pepper",
        "white pepper",
        "potatoes peeled and cut into cubes",
        "For serving: chopped walnuts and extra honey",
        "Salt",
        "pepper",
    ]


def test_recipe_items_single_line_and_header():
    data = {"recipeIngredient": ["For the sauce:", "1 cup milk", "2 eggs"]}
    assert recipe_shopping_items(data, 0) == []
    assert [i["item_name"] for i in recipe_shopping_items(data, 2)] == ["eggs"]


async def test_alternative_merges_with_existing_item(
    client: AsyncClient, auth_headers, db, test_user, test_household, shopping_list
):
    db.add(
        ShoppingListItem(
            list_id=shopping_list.id,
            item_name="unsalted butter",
            quantity="2",
            unit="tablespoon",
            checked=False,
            display_order=1,
        )
    )
    r = Recipe(
        user_id=test_user.id,
        household_id=test_household["id"],
        name="Saute",
        recipe_data={"recipeIngredient": ["2 tablespoons unsalted butter or olive oil"]},
    )
    db.add(r)
    await db.commit()
    res = await client.post(
        f"{BASE}/from-recipe",
        json={"recipe_id": r.id, "shopping_list_id": shopping_list.id, "ingredient_index": 0},
        headers=auth_headers,
    )
    items = {i["item_name"]: i["quantity"] for i in res.json()["items"]}
    assert items == {"unsalted butter": "4", "olive oil": "2"}


async def test_from_recipe_into_existing_list_merges(
    client: AsyncClient, auth_headers, recipe, shopping_list
):
    await client.post(
        f"{BASE}/{shopping_list.id}/items",
        json={"item_name": "flour", "quantity": "1", "unit": "cup"},
        headers=auth_headers,
    )
    res = await client.post(
        f"{BASE}/from-recipe",
        json={"recipe_id": recipe.id, "shopping_list_id": shopping_list.id},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == shopping_list.id
    flour = [i for i in body["items"] if i["item_name"] == "flour"]
    assert len(flour) == 1
    assert flour[0]["quantity"] == "3"


async def test_from_meal_plan_into_existing_list_merges(
    client: AsyncClient, auth_headers, db, recipe, shopping_list, test_user, test_household
):
    plan = MealPlan(
        household_id=test_household["id"],
        week_start_date=date(2026, 11, 2),
        created_by_user_id=test_user.id,
    )
    db.add(plan)
    await db.flush()
    db.add(
        PlannedMeal(meal_plan_id=plan.id, recipe_id=recipe.id, day_of_week=0, meal_type="dinner")
    )
    await db.commit()
    await client.post(
        f"{BASE}/{shopping_list.id}/items",
        json={"item_name": "egg", "quantity": "1"},
        headers=auth_headers,
    )
    res = await client.post(
        f"{BASE}/from-meal-plan",
        json={"meal_plan_id": plan.id, "shopping_list_id": shopping_list.id},
        headers=auth_headers,
    )
    assert res.status_code == 200
    eggs = [i for i in res.json()["items"] if i["item_name"] == "egg"]
    assert len(eggs) == 1
    assert eggs[0]["quantity"] == "3"


async def _other_household_list(client: AsyncClient) -> int:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "SecurePass123!", "display_name": "Other"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": "other@example.com", "password": "SecurePass123!"}
    )
    headers = {"Authorization": f"Bearer {login.cookies.get('access_token')}"}
    created = await client.post(f"{BASE}/", json={"name": "Theirs"}, headers=headers)
    assert created.status_code == 201
    return created.json()["id"]


async def test_cross_household_list_is_404(client: AsyncClient, auth_headers, recipe):
    other_id = await _other_household_list(client)
    responses = [
        await client.post(
            f"{BASE}/{other_id}/items", json={"item_name": "x"}, headers=auth_headers
        ),
        await client.post(
            f"{BASE}/from-recipe",
            json={"recipe_id": recipe.id, "shopping_list_id": other_id},
            headers=auth_headers,
        ),
    ]
    for res in responses:
        assert res.status_code == 404
        assert res.json()["error_code"] == "SHOPPING_LIST_NOT_FOUND"


async def test_created_by_name_in_summary_and_detail(
    client: AsyncClient, auth_headers, shopping_list, test_user
):
    summaries = (await client.get(f"{BASE}/", headers=auth_headers)).json()
    assert summaries[0]["created_by_user_id"] == test_user.id
    assert summaries[0]["created_by_name"] == "Test User"
    detail = (await client.get(f"{BASE}/{shopping_list.id}", headers=auth_headers)).json()
    assert detail["created_by_name"] == "Test User"
