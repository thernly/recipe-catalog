"""Shopping-list generation from recipes and meal plans."""

from datetime import date

from sqlalchemy import select

from app.models.meal_plan import MealPlan, PlannedMeal
from app.models.recipe import Recipe
from app.models.user import User
from app.services import household as household_service
from app.services.recipe_cleanup import clean_recipe_data


LINES = ["2 cups flour, sifted", "2 eggs", "1-2 tbsp oil", "For the sauce:"]


async def _recipe(test_db, recipe_data):
    user = (
        await test_db.execute(select(User).where(User.email == "testuser@example.com"))
    ).scalar_one()
    household = await household_service.get_user_household(test_db, user.id)
    recipe = Recipe(
        user_id=user.id, household_id=household.id, name="Cake", recipe_data=recipe_data
    )
    test_db.add(recipe)
    await test_db.commit()
    return user, household, recipe


async def test_from_recipe_uses_parsed_ingredients(client, test_db, test_user_headers):
    _, _, recipe = await _recipe(test_db, clean_recipe_data({"recipeIngredient": LINES}).data)
    response = await client.post(
        "/api/v1/shopping-lists/from-recipe",
        json={"recipe_id": recipe.id},
        headers=test_user_headers,
    )
    assert response.status_code == 200, response.text
    items = [
        (i["quantity"], i["unit"], i["item_name"], i["notes"]) for i in response.json()["items"]
    ]
    assert items == [
        ("2", "cup", "flour", None),  # prep notes stay off the list
        ("2", None, "eggs", None),
        ("2", "tablespoon", "oil", None),  # range: the upper bound
    ]


async def test_from_recipe_legacy_without_parsed(client, test_db, test_user_headers):
    _, _, recipe = await _recipe(test_db, {"recipeIngredient": ["2 eggs", "salt"]})
    response = await client.post(
        "/api/v1/shopping-lists/from-recipe",
        json={"recipe_id": recipe.id},
        headers=test_user_headers,
    )
    assert response.status_code == 200, response.text
    items = [(i["quantity"], i["item_name"]) for i in response.json()["items"]]
    assert items == [("2", "eggs"), (None, "salt")]


async def test_from_meal_plan_numeric_quantities(client, test_db, test_user_headers):
    user, household, recipe = await _recipe(
        test_db, clean_recipe_data({"recipeIngredient": LINES}).data
    )
    plan = MealPlan(
        household_id=household.id, week_start_date=date(2026, 11, 2), created_by_user_id=user.id
    )
    test_db.add(plan)
    await test_db.flush()
    test_db.add(
        PlannedMeal(
            meal_plan_id=plan.id,
            recipe_id=recipe.id,
            created_by_user_id=user.id,
            day_of_week=0,
            meal_type="dinner",
        )
    )
    await test_db.commit()
    response = await client.post(
        "/api/v1/shopping-lists/from-meal-plan",
        json={"meal_plan_id": plan.id},
        headers=test_user_headers,
    )
    assert response.status_code == 200, response.text
    items = {i["item_name"]: i for i in response.json()["items"]}
    assert "for the sauce:" not in items
    egg = next(v for k, v in items.items() if k.startswith("egg"))
    assert float(egg["quantity"]) == 2 and egg["unit"] is None
    oil = items["oil"]
    assert float(oil["quantity"]) == 2
