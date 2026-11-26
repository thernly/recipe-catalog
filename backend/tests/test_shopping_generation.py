"""Shopping-list generation from recipes and meal plans."""

from datetime import date

import pytest
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
        # the note says which recipe; prep notes ("sifted") stay off the list
        ("2", "cup", "flour", "for Cake"),
        ("2", None, "eggs", "for Cake"),
        ("2", "tablespoon", "oil", "for Cake"),  # range: the upper bound
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


async def test_meal_plan_preview_matches_the_generated_list_and_saves_nothing(
    client, test_db, test_user_headers
):
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
            servings=None,
        )
    )
    await test_db.commit()
    body = {"meal_plan_id": plan.id}

    preview = await client.post(
        "/api/v1/shopping-lists/from-meal-plan/preview", json=body, headers=test_user_headers
    )

    assert preview.status_code == 200, preview.text
    assert (await client.get("/api/v1/shopping-lists/", headers=test_user_headers)).json() == []
    made = await client.post(
        "/api/v1/shopping-lists/from-meal-plan", json=body, headers=test_user_headers
    )
    fields = ("item_name", "quantity", "unit", "notes")
    assert preview.json() == [{f: item[f] for f in fields} for item in made.json()["items"]]
    assert [item["item_name"] for item in preview.json()] == ["flour", "egg", "oil"]


async def test_meal_plan_preview_adds_related_units_like_the_generated_list(
    client, test_db, test_user_headers
):
    """Two meals with the same ingredient in grams and in kilograms: one line, not two."""
    user, household, cake = await _recipe(
        test_db, clean_recipe_data({"recipeIngredient": ["250 g butter", "1 tbsp salt"]}).data
    )
    pie = Recipe(
        user_id=user.id,
        household_id=household.id,
        name="Pie",
        recipe_data=clean_recipe_data({"recipeIngredient": ["1 kg butter", "3 tsp salt"]}).data,
    )
    plan = MealPlan(
        household_id=household.id, week_start_date=date(2026, 11, 2), created_by_user_id=user.id
    )
    test_db.add_all([pie, plan])
    await test_db.flush()
    for day, recipe in enumerate([cake, pie]):
        test_db.add(
            PlannedMeal(
                meal_plan_id=plan.id,
                recipe_id=recipe.id,
                created_by_user_id=user.id,
                day_of_week=day,
                meal_type="dinner",
            )
        )
    await test_db.commit()
    body = {"meal_plan_id": plan.id}

    preview = await client.post(
        "/api/v1/shopping-lists/from-meal-plan/preview", json=body, headers=test_user_headers
    )
    made = await client.post(
        "/api/v1/shopping-lists/from-meal-plan", json=body, headers=test_user_headers
    )

    fields = ("item_name", "quantity", "unit", "notes")
    assert preview.json() == [{f: item[f] for f in fields} for item in made.json()["items"]]
    assert [(i["item_name"], i["quantity"], i["unit"]) for i in preview.json()] == [
        ("butter", "1 1/4", "kilogram"),
        ("salt", "2", "tablespoon"),
    ]


async def test_meal_plan_preview_is_household_scoped(client, test_db, test_user_headers):
    from tests.test_recipe_notes import _login

    user, household, _ = await _recipe(test_db, {"recipeIngredient": ["2 eggs"]})
    plan = MealPlan(
        household_id=household.id, week_start_date=date(2026, 11, 2), created_by_user_id=user.id
    )
    test_db.add(plan)
    await test_db.commit()
    stranger = await _login(client, "stranger@example.com")

    response = await client.post(
        "/api/v1/shopping-lists/from-meal-plan/preview",
        json={"meal_plan_id": plan.id},
        headers=stranger,
    )

    assert response.status_code == 404


async def test_from_meal_plan_notes_which_recipes_each_item_is_for(
    client, test_db, test_user_headers
):
    user, household, cake = await _recipe(test_db, {"recipeIngredient": ["2 eggs", "1 cup flour"]})
    omelette = Recipe(
        user_id=user.id,
        household_id=household.id,
        name="Omelette",
        recipe_data={"recipeIngredient": ["3 eggs", "1 tbsp butter"]},
    )
    plan = MealPlan(
        household_id=household.id, week_start_date=date(2026, 11, 2), created_by_user_id=user.id
    )
    test_db.add_all([omelette, plan])
    await test_db.flush()
    test_db.add_all(
        [
            PlannedMeal(
                meal_plan_id=plan.id,
                recipe_id=recipe_id,
                created_by_user_id=user.id,
                day_of_week=day,
                meal_type="dinner",
            )
            # Cake twice: its name is noted once
            for day, recipe_id in enumerate([cake.id, omelette.id, cake.id])
        ]
    )
    await test_db.commit()

    response = await client.post(
        "/api/v1/shopping-lists/from-meal-plan",
        json={"meal_plan_id": plan.id},
        headers=test_user_headers,
    )

    assert response.status_code == 200, response.text
    notes = {i["item_name"]: i["notes"] for i in response.json()["items"]}
    assert notes == {
        "egg": "for Cake; for Omelette",
        "flour": "for Cake",
        "butter": "for Omelette",
    }


@pytest.mark.parametrize(
    ("recipe_yield", "servings", "eggs", "flour"),
    [
        ("4 servings", 8, "4", "4"),
        ("4 servings", 2, "1", "1"),
        ("4 servings", 6, "3", "3"),
        ("Serves 4", 8, "4", "4"),
        (4, 8, "4", "4"),  # recipes saved before yields were normalized to text
        ("4-6 servings", 8, "4", "4"),  # a range scales from its lower bound
        ("4 servings", 3, "1 1/2", "1 1/2"),
        ("4 servings", None, "2", "2"),  # no planned servings: as written
        ("1 loaf", 8, "2", "2"),  # not counted in servings: as written
        ("12 cookies", 4, "2", "2"),
        (None, 8, "2", "2"),
    ],
)
async def test_from_meal_plan_scales_by_planned_servings(
    client, test_db, test_user_headers, recipe_yield, servings, eggs, flour
):
    data = clean_recipe_data({"recipeIngredient": LINES}).data
    if recipe_yield is not None:
        data["recipeYield"] = recipe_yield
    user, household, recipe = await _recipe(test_db, data)
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
            servings=servings,
        )
    )
    await test_db.commit()
    response = await client.post(
        "/api/v1/shopping-lists/from-meal-plan",
        json={"meal_plan_id": plan.id},
        headers=test_user_headers,
    )
    assert response.status_code == 200, response.text
    items = {i["item_name"]: i["quantity"] for i in response.json()["items"]}
    assert (items["egg"], items["flour"]) == (eggs, flour)
