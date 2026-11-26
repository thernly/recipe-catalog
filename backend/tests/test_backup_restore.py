"""Complete Backup: export, then restore into an account that lost the data."""

import json
from datetime import date
from io import BytesIO

from sqlalchemy import delete, func, select

from app.models.collection import Collection, RecipeCollection
from app.models.meal_plan import MealPlan, PlannedMeal
from app.models.recipe import Recipe
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.user import User
from app.services import household as household_service


RESTORE_URL = "/api/v1/import/backup"
TABLES = (PlannedMeal, MealPlan, ShoppingListItem, ShoppingList, RecipeCollection, Recipe)


async def _seed(test_db):
    """One recipe in a collection, on a meal plan, plus a shopping list."""
    user = (
        await test_db.execute(select(User).where(User.email == "testuser@example.com"))
    ).scalar_one()
    household = await household_service.get_user_household(test_db, user.id)
    recipe = Recipe(
        user_id=user.id,
        household_id=household.id,
        name="Dal",
        source_url="https://example.com/dal",
        source_type="manual",
        recipe_data={"recipeIngredient": ["1 cup lentils"], "recipeYield": "4 servings"},
    )
    collection = Collection(user_id=user.id, household_id=household.id, name="Weeknight")
    plan = MealPlan(
        household_id=household.id, week_start_date=date(2026, 11, 2), created_by_user_id=user.id
    )
    shopping = ShoppingList(
        household_id=household.id, name="Saturday shop", status="active", created_by_user_id=user.id
    )
    test_db.add_all([recipe, collection, plan, shopping])
    await test_db.flush()
    test_db.add_all(
        [
            RecipeCollection(recipe_id=recipe.id, collection_id=collection.id),
            PlannedMeal(
                meal_plan_id=plan.id,
                recipe_id=recipe.id,
                created_by_user_id=user.id,
                day_of_week=2,
                meal_type="dinner",
                servings=6,
                notes="double the garlic",
            ),
            ShoppingListItem(
                list_id=shopping.id, item_name="milk", quantity="2", unit="litre", checked=True
            ),
        ]
    )
    await test_db.commit()


async def _wipe(test_db):
    for table in TABLES:
        await test_db.execute(delete(table))
    await test_db.execute(delete(Collection).where(Collection.name == "Weeknight"))
    await test_db.commit()


async def _counts(test_db):
    test_db.expire_all()
    return [
        (await test_db.execute(select(func.count()).select_from(table))).scalar_one()
        for table in TABLES
    ]


async def _backup(client, headers) -> bytes:
    response = await client.get("/api/v1/export/all", headers=headers)
    assert response.status_code == 200, response.text
    return response.content


async def _restore(client, headers, content: bytes, scope: str | None = None):
    return await client.post(
        RESTORE_URL,
        files={"file": ("backup.json", BytesIO(content), "application/json")},
        data={"scope": scope} if scope else {},
        headers=headers,
    )


async def test_backup_contains_meal_plans_and_shopping_lists(client, test_db, test_user_headers):
    await _seed(test_db)
    data = json.loads(await _backup(client, test_user_headers))

    recipe_id = data["recipes"][0]["id"]
    assert data["meal_plans"] == [
        {
            "week_start_date": "2026-11-02",
            "meals": [
                {
                    "recipe_id": recipe_id,
                    "title": None,
                    "day_of_week": 2,
                    "meal_type": "dinner",
                    "servings": 6,
                    "notes": "double the garlic",
                }
            ],
        }
    ]
    (shopping,) = data["shopping_lists"]
    assert shopping["name"] == "Saturday shop"
    assert [
        (i["item_name"], i["quantity"], i["unit"], i["checked"]) for i in shopping["items"]
    ] == [("milk", "2", "litre", True)]


async def test_restore_everything_then_again_adds_nothing(client, test_db, test_user_headers):
    await _seed(test_db)
    content = await _backup(client, test_user_headers)
    await _wipe(test_db)

    response = await _restore(client, test_user_headers, content)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["details"]["created"] == 1
    assert body["restored"] == {
        "collections": 1,
        "collection_recipes": 1,
        "meal_plans": 1,
        "planned_meals": 1,
        "planned_meals_skipped": 0,
        "shopping_lists": 1,
        "shopping_lists_skipped": 0,
    }
    assert await _counts(test_db) == [1, 1, 1, 1, 1, 1]

    # Links point at the new recipe row, and the details came back with them
    recipe = (await test_db.execute(select(Recipe))).scalar_one()
    assert (recipe.name, recipe.source_type) == ("Dal", "manual")
    meal = (await test_db.execute(select(PlannedMeal))).scalar_one()
    assert (meal.recipe_id, meal.day_of_week, meal.meal_type, meal.servings, meal.notes) == (
        recipe.id,
        2,
        "dinner",
        6,
        "double the garlic",
    )
    link = (await test_db.execute(select(RecipeCollection))).scalar_one()
    assert link.recipe_id == recipe.id
    item = (await test_db.execute(select(ShoppingListItem))).scalar_one()
    assert (item.item_name, item.quantity, item.unit, item.checked) == ("milk", "2", "litre", True)

    again = await _restore(client, test_user_headers, content)

    assert again.status_code == 200, again.text
    assert again.json()["details"]["skipped"] == 1
    assert again.json()["restored"] == {
        "collections": 0,
        "collection_recipes": 0,
        "meal_plans": 0,
        "planned_meals": 0,
        "planned_meals_skipped": 0,
        "shopping_lists": 0,
        "shopping_lists_skipped": 1,
    }
    assert await _counts(test_db) == [1, 1, 1, 1, 1, 1]


async def test_restore_recipes_only(client, test_db, test_user_headers):
    await _seed(test_db)
    content = await _backup(client, test_user_headers)
    await _wipe(test_db)

    response = await _restore(client, test_user_headers, content, scope="recipes")

    assert response.status_code == 200, response.text
    assert response.json()["restored"] is None
    assert await _counts(test_db) == [0, 0, 0, 0, 0, 1]


async def test_restore_skips_meals_whose_recipe_is_not_in_the_backup(
    client, test_db, test_user_headers
):
    await _seed(test_db)
    data = json.loads(await _backup(client, test_user_headers))
    data["meal_plans"][0]["meals"][0]["recipe_id"] = 999_999  # e.g. another member's recipe
    await _wipe(test_db)

    response = await _restore(client, test_user_headers, json.dumps(data).encode())

    assert response.status_code == 200, response.text
    restored = response.json()["restored"]
    assert (restored["planned_meals"], restored["planned_meals_skipped"]) == (0, 1)


async def test_restore_tolerates_malformed_sections(client, test_db, test_user_headers):
    backup = {
        "export_type": "complete_backup",
        "recipes": [{"name": "Soup", "recipe_data": {"recipeIngredient": ["water"]}}, "junk"],
        "collections": [None, {"name": 5}],
        "meal_plans": [{"week_start_date": "not a date", "meals": [{}]}, 7],
        "shopping_lists": [{"name": "Shop", "items": ["junk", {"item_name": "eggs"}]}, {}],
    }

    response = await _restore(client, test_user_headers, json.dumps(backup).encode())

    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["details"]["created"], body["details"]["failed"]) == (1, 1)
    assert body["restored"]["shopping_lists"] == 1
    item = (await test_db.execute(select(ShoppingListItem))).scalar_one()
    assert item.item_name == "eggs"


async def test_restore_rejects_a_file_that_is_not_a_backup(client, test_user_headers):
    response = await _restore(client, test_user_headers, json.dumps([{"name": "Soup"}]).encode())

    assert response.status_code == 400
    assert "Complete Backup" in response.json()["message"]
