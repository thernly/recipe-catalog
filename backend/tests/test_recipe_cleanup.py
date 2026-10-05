"""Tests for the shared recipe cleanup and its use on every write path."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe
from app.services.ingredient_parser import PARSED_BY_MODEL
from app.services.recipe_cleanup import (
    clean_recipe_data,
    derive_total_time_minutes,
    format_iso_duration,
    normalize_time,
    normalize_yield,
    parse_duration_minutes,
)


# ----------------------------------------------------------------------------
# Durations
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "minutes"),
    [
        ("PT30M", 30),
        ("PT1H30M", 90),
        ("PT90M", 90),
        ("PT2H", 120),
        ("P0DT1H15M", 75),
        ("P1D", 1440),
        ("PT1H30M0S", 90),
        ("PT0M", 0),
        ("pt45m", 45),
        ("30 minutes", 30),
        ("45 mins", 45),
        ("1 hour", 60),
        ("1 hour 30 minutes", 90),
        ("2 hrs 15 mins", 135),
        ("1 1/2 hours", 90),
        ("1½ hours", 90),
        ("1.5 hrs", 90),
        ("1h30m", 90),
        ("20-25 mins", 25),
        (45, 45),
    ],
)
def test_parse_duration_minutes(value, minutes):
    assert parse_duration_minutes(value) == minutes


@pytest.mark.parametrize("value", ["", None, "overnight", "some text", "PT", "P", True, -5])
def test_parse_duration_minutes_unreadable(value):
    assert parse_duration_minutes(value) is None


@pytest.mark.parametrize(
    ("minutes", "iso"), [(0, "PT0M"), (30, "PT30M"), (60, "PT1H"), (90, "PT1H30M"), (1500, "PT25H")]
)
def test_format_iso_duration(minutes, iso):
    assert format_iso_duration(minutes) == iso


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1 hr 30 mins", "PT1H30M"),
        ("PT90M", "PT1H30M"),
        ("P0DT0H20M", "PT20M"),
        ("PT1H", "PT1H"),
        ("overnight", "overnight"),
        (" chill overnight ", "chill overnight"),
        ("", ""),
        (None, None),
    ],
)
def test_normalize_time(value, expected):
    assert normalize_time(value) == expected


# ----------------------------------------------------------------------------
# Yield
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("6 6 servings", "6 servings"),
        ("4 servings 4 servings", "4 servings"),
        ("4  servings", "4 servings"),
        ("Servings: 4", "4"),
        ("Yield: 12 cookies", "12 cookies"),
        ("Makes 12 cookies", "Makes 12 cookies"),
        ("1 1/2 cups", "1 1/2 cups"),
        ("1 1/2 1 1/2 cups", "1 1/2 cups"),
        ("2 2.5 cups", "2 2.5 cups"),
        (["4", "4 servings"], "4 servings"),
        (["8"], "8"),
        (["", "6 6 servings"], "6 servings"),
        (6, "6"),
        (2.5, "2.5"),
        ("", ""),
        (None, None),
        ([], []),
        ({"value": 4}, {"value": 4}),
    ],
)
def test_normalize_yield(value, expected):
    assert normalize_yield(value) == expected


# ----------------------------------------------------------------------------
# clean_recipe_data
# ----------------------------------------------------------------------------


def test_clean_recipe_data_writes_in_place_and_keeps_lines_verbatim():
    original = {
        "name": "Soup",
        "recipeYield": "6 6 servings",
        "prepTime": "15 mins",
        "cookTime": "PT1H",
        "recipeIngredient": ["2 cups stock", "Juice of 1 lemon"],
    }
    result = clean_recipe_data(original)

    assert result.data["recipeYield"] == "6 servings"
    assert result.data["prepTime"] == "PT15M"
    assert result.data["cookTime"] == "PT1H"
    assert result.data["recipeIngredient"] == ["2 cups stock", "Juice of 1 lemon"]
    assert [e["raw"] for e in result.data["parsedIngredients"]] == original["recipeIngredient"]
    assert result.changes == {
        "recipeYield": ("6 6 servings", "6 servings"),
        "prepTime": ("15 mins", "PT15M"),
    }
    assert (result.ingredient_lines, result.parsed_lines) == (2, 1)
    assert result.unparsed == ["Juice of 1 lemon"]
    # The input is not modified
    assert original["recipeYield"] == "6 6 servings"
    assert "parsedIngredients" not in original


def test_clean_recipe_data_header_lines_are_not_counted():
    result = clean_recipe_data({"recipeIngredient": ["For the dough:", "2 cups flour"]})
    assert (result.ingredient_lines, result.parsed_lines) == (1, 1)


def test_clean_recipe_data_does_not_add_missing_fields():
    result = clean_recipe_data({"name": "Toast"})
    assert set(result.data) == {"name", "parsedIngredients"}
    assert result.data["parsedIngredients"] == []


def test_clean_recipe_data_is_idempotent():
    first = clean_recipe_data(
        {"recipeYield": ["4", "4 servings"], "totalTime": "1 hour", "recipeIngredient": ["1 egg"]}
    )
    second = clean_recipe_data(first.data, first.data["parsedIngredients"])
    assert second.data == first.data
    assert second.changes == {}


def test_clean_recipe_data_ignores_client_parsed_ingredients():
    forged = [{"raw": "2 cups flour", "item": "gold", "parsedBy": "model"}]
    result = clean_recipe_data({"recipeIngredient": ["1 egg"], "parsedIngredients": forged})
    assert result.data["parsedIngredients"][0]["raw"] == "1 egg"
    assert result.data["parsedIngredients"][0]["item"] == "egg"


@pytest.mark.parametrize(
    ("data", "minutes"),
    [
        ({"totalTime": "PT45M", "prepTime": "PT10M"}, 45),
        ({"prepTime": "PT10M", "cookTime": "PT20M"}, 30),
        ({"cookTime": "1 hour"}, 60),
        ({"totalTime": "overnight"}, None),
        ({}, None),
    ],
)
def test_derive_total_time_minutes(data, minutes):
    assert derive_total_time_minutes(data) == minutes


# ----------------------------------------------------------------------------
# Write paths
# ----------------------------------------------------------------------------

MESSY = {
    "recipeYield": "6 6 servings",
    "prepTime": "15 mins",
    "cookTime": "1 hr",
    "recipeIngredient": ["2 cups flour, sifted", "For the glaze:", "1 cup sugar"],
    "recipeInstructions": ["Mix.", "Bake."],
}


def _assert_cleaned(recipe_data: dict) -> None:
    assert recipe_data["recipeYield"] == "6 servings"
    assert recipe_data["prepTime"] == "PT15M"
    assert recipe_data["cookTime"] == "PT1H"
    assert recipe_data["recipeIngredient"] == MESSY["recipeIngredient"]
    parsed = recipe_data["parsedIngredients"]
    assert [e["raw"] for e in parsed] == MESSY["recipeIngredient"]
    assert parsed[0]["item"] == "flour"
    assert parsed[0]["note"] == "sifted"
    assert parsed[2]["group"] == "For the glaze"


async def test_create_recipe_is_cleaned(client: AsyncClient, test_user_headers: dict):
    response = await client.post(
        "/api/v1/recipes/",
        json={"name": "Cake", "recipe_data": {"name": "Cake", **MESSY}},
        headers=test_user_headers,
    )

    assert response.status_code == 201
    body = response.json()
    _assert_cleaned(body["recipe_data"])
    # Filled from the cleaned times because the client sent none
    assert body["total_time_minutes"] == 75


async def test_create_recipe_keeps_client_total_time(client: AsyncClient, test_user_headers: dict):
    response = await client.post(
        "/api/v1/recipes/",
        json={
            "name": "Cake",
            "total_time_minutes": 90,
            "recipe_data": {"name": "Cake", **MESSY},
        },
        headers=test_user_headers,
    )
    assert response.json()["total_time_minutes"] == 90


async def test_update_recipe_is_cleaned_and_keeps_model_parses(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    created = (
        await client.post(
            "/api/v1/recipes/",
            json={
                "name": "Lemonade",
                "recipe_data": {"recipeIngredient": ["Juice of 1 lemon", "1 cup water"]},
            },
            headers=test_user_headers,
        )
    ).json()

    # Simulate a model parse stored for the line the regex could not handle
    recipe = (await db.execute(select(Recipe).where(Recipe.id == created["id"]))).scalar_one()
    data = dict(recipe.recipe_data)
    parsed = [dict(e) for e in data["parsedIngredients"]]
    parsed[0].update(quantity=1, item="lemon", note="juiced", parsedBy=PARSED_BY_MODEL)
    data["parsedIngredients"] = parsed
    recipe.recipe_data = data
    await db.commit()

    # The form sends the edited recipe without parsedIngredients
    response = await client.patch(
        f"/api/v1/recipes/{created['id']}",
        json={
            "recipe_data": {
                **MESSY,
                "recipeIngredient": ["Juice of 1 lemon", "2 cups water"],
            }
        },
        headers=test_user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recipe_data"]["recipeYield"] == "6 servings"
    parsed = body["recipe_data"]["parsedIngredients"]
    assert parsed[0]["parsedBy"] == PARSED_BY_MODEL
    assert parsed[0]["item"] == "lemon"
    assert parsed[1]["quantity"] == 2
    assert body["total_time_minutes"] == 75


async def test_update_recipe_ignores_client_parsed_ingredients(
    client: AsyncClient, test_user_headers: dict
):
    created = (
        await client.post(
            "/api/v1/recipes/",
            json={"name": "Eggs", "recipe_data": {"recipeIngredient": ["2 eggs"]}},
            headers=test_user_headers,
        )
    ).json()

    response = await client.patch(
        f"/api/v1/recipes/{created['id']}",
        json={
            "recipe_data": {
                "recipeIngredient": ["2 eggs"],
                "parsedIngredients": [{"raw": "2 eggs", "item": "gold", "parsedBy": "model"}],
            }
        },
        headers=test_user_headers,
    )

    entry = response.json()["recipe_data"]["parsedIngredients"][0]
    assert entry["item"] == "eggs"
    assert entry["parsedBy"] == "regex"


async def test_update_without_recipe_data_leaves_it_alone(
    client: AsyncClient, test_user_headers: dict
):
    created = (
        await client.post(
            "/api/v1/recipes/",
            json={"name": "Eggs", "recipe_data": {"recipeIngredient": ["2 eggs"]}},
            headers=test_user_headers,
        )
    ).json()

    response = await client.patch(
        f"/api/v1/recipes/{created['id']}", json={"name": "Boiled eggs"}, headers=test_user_headers
    )
    assert response.json()["recipe_data"] == created["recipe_data"]


async def test_import_json_is_cleaned(client: AsyncClient, test_user_headers: dict):
    response = await client.post(
        "/api/v1/import/recipes/json",
        json=[{"name": "Imported Cake", **MESSY}],
        headers=test_user_headers,
    )

    recipe_id = response.json()["details"]["items"][0]["recipe_id"]
    recipe = (await client.get(f"/api/v1/recipes/{recipe_id}", headers=test_user_headers)).json()
    _assert_cleaned(recipe["recipe_data"])
    assert recipe["total_time_minutes"] == 75


async def test_intake_is_cleaned_and_update_keeps_model_parses(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    payload = {"name": "Siphon Cake", **MESSY, "recipeIngredient": ["Juice of 1 lemon"]}
    created = (await client.post("/api/v1/intake", json=payload, headers=test_user_headers)).json()

    recipe = (await db.execute(select(Recipe).where(Recipe.id == created["id"]))).scalar_one()
    assert recipe.recipe_data["recipeYield"] == "6 servings"
    data = dict(recipe.recipe_data)
    data["parsedIngredients"] = [
        {**data["parsedIngredients"][0], "item": "lemon", "parsedBy": PARSED_BY_MODEL}
    ]
    recipe.recipe_data = data
    await db.commit()

    updated = await client.post(
        "/api/v1/intake?on_duplicate=update", json=payload, headers=test_user_headers
    )
    assert updated.json()["status"] == "updated"

    await db.refresh(recipe)
    assert recipe.recipe_data["parsedIngredients"][0]["parsedBy"] == PARSED_BY_MODEL
    assert recipe.recipe_data["parsedIngredients"][0]["item"] == "lemon"


async def test_skipped_intake_does_not_touch_existing_recipe(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    payload = {"name": "Siphon Cake", "recipeYield": "4 servings"}
    created = (await client.post("/api/v1/intake", json=payload, headers=test_user_headers)).json()

    skipped = await client.post(
        "/api/v1/intake",
        json={**payload, "recipeYield": "8 8 servings"},
        headers=test_user_headers,
    )
    assert skipped.json()["status"] == "skipped"

    recipe = (await db.execute(select(Recipe).where(Recipe.id == created["id"]))).scalar_one()
    await db.refresh(recipe)
    assert recipe.recipe_data["recipeYield"] == "4 servings"
