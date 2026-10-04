"""Tests for the intake routes and personal-API-token authentication."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.api_token import ApiToken
from app.models.household import HouseholdMember
from app.models.recipe import Recipe
from app.models.user import User
from app.utils.safe_fetch import FetchResult


INTAKE_URL = "/api/v1/intake"
CHECK_URL = "/api/v1/intake/check"

SIPHON_RECIPE = {
    "@context": "https://schema.org",
    "@type": "Recipe",
    "name": "Weeknight Dal",
    "description": "Red lentils with spices",
    "url": "https://example.com/dal",
    "recipeYield": "4 servings",
    "prepTime": "PT10M",
    "cookTime": "PT25M",
    "recipeCategory": ["Dinner"],
    "recipeCuisine": "Indian",
    "recipeIngredient": ["1 cup red lentils", "2 cups water"],
    "recipeInstructions": [{"@type": "HowToStep", "text": "Simmer until soft."}],
}


@pytest.fixture
async def api_token(client: AsyncClient, test_user_headers: dict) -> str:
    response = await client.post(
        "/api/v1/users/me/api-tokens", json={"name": "Siphon"}, headers=test_user_headers
    )
    return response.json()["token"]


@pytest.fixture
def token_headers(api_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_token}"}


async def test_check_valid_token(client: AsyncClient, token_headers: dict, db: AsyncSession):
    client.cookies.clear()
    response = await client.get(CHECK_URL, headers=token_headers)

    assert response.status_code == 200
    assert response.json()["success"] is True

    row = (await db.execute(select(ApiToken))).scalar_one()
    await db.refresh(row)
    assert row.last_used_at is not None


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer rcat_not-a-real-token"},
        {"Authorization": "Bearer not-a-jwt"},
    ],
)
async def test_check_rejects_missing_or_bad_token(client: AsyncClient, headers: dict):
    client.cookies.clear()
    response = await client.get(CHECK_URL, headers=headers)

    assert response.status_code == 401
    body = response.json()
    assert body["error_code"] == "UNAUTHORIZED"
    assert body["message"]


async def test_bad_token_does_not_fall_back_to_session(
    client: AsyncClient, test_user_headers: dict
):
    """A signed-in browser sending a bogus token is still refused."""
    assert client.cookies.get("access_token")  # session cookie present
    response = await client.get(
        CHECK_URL, headers={"Authorization": "Bearer rcat_not-a-real-token"}
    )
    assert response.status_code == 401


async def test_revoked_token_is_rejected(
    client: AsyncClient, test_user_headers: dict, api_token: str, token_headers: dict
):
    listed = (await client.get("/api/v1/users/me/api-tokens", headers=test_user_headers)).json()
    await client.delete(f"/api/v1/users/me/api-tokens/{listed[0]['id']}", headers=test_user_headers)
    client.cookies.clear()

    assert (await client.get(CHECK_URL, headers=token_headers)).status_code == 401
    assert (
        await client.post(INTAKE_URL, json=SIPHON_RECIPE, headers=token_headers)
    ).status_code == 401


async def test_inactive_user_token_is_rejected(
    client: AsyncClient, token_headers: dict, db: AsyncSession
):
    user = (await db.execute(select(User).where(User.email == "testuser@example.com"))).scalar_one()
    user.is_active = False
    await db.commit()
    client.cookies.clear()

    assert (await client.get(CHECK_URL, headers=token_headers)).status_code == 403


async def test_intake_creates_recipe(
    client: AsyncClient, test_user_headers: dict, token_headers: dict, db: AsyncSession
):
    client.cookies.clear()
    response = await client.post(INTAKE_URL, json=SIPHON_RECIPE, headers=token_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["status"] == "created"
    assert isinstance(body["id"], int)
    assert body["message"]
    assert body["url"] == f"{settings.FRONTEND_URL.rstrip('/')}/recipes/{body['id']}"

    # Saved like a file import: owner, household, denormalized columns, schema.org data
    recipe = (await db.execute(select(Recipe).where(Recipe.id == body["id"]))).scalar_one()
    user = (await db.execute(select(User).where(User.email == "testuser@example.com"))).scalar_one()
    member = (
        await db.execute(select(HouseholdMember).where(HouseholdMember.user_id == user.id))
    ).scalar_one()
    assert recipe.user_id == user.id
    assert recipe.household_id == member.household_id
    assert recipe.name == "Weeknight Dal"
    assert recipe.cuisine == "Indian"
    assert recipe.category == "Dinner"
    assert recipe.total_time_minutes == 35
    assert recipe.source_url == "https://example.com/dal"
    assert recipe.source_type == "imported"
    assert recipe.recipe_data["recipeIngredient"] == SIPHON_RECIPE["recipeIngredient"]
    assert recipe.recipe_data["recipeYield"] == "4 servings"


async def test_intake_skips_duplicate_name(client: AsyncClient, token_headers: dict):
    client.cookies.clear()
    first = (await client.post(INTAKE_URL, json=SIPHON_RECIPE, headers=token_headers)).json()
    second = await client.post(INTAKE_URL, json=SIPHON_RECIPE, headers=token_headers)

    assert second.status_code == 200
    body = second.json()
    assert body["status"] == "skipped"
    assert body["id"] == first["id"]
    assert body["url"].endswith(f"/recipes/{first['id']}")


async def test_intake_updates_duplicate_when_requested(
    client: AsyncClient, token_headers: dict, db: AsyncSession
):
    client.cookies.clear()
    first = (await client.post(INTAKE_URL, json=SIPHON_RECIPE, headers=token_headers)).json()
    improved = {**SIPHON_RECIPE, "notes": "Rinse the lentils first."}
    second = await client.post(
        INTAKE_URL, params={"on_duplicate": "update"}, json=improved, headers=token_headers
    )

    assert second.status_code == 200
    body = second.json()
    assert body["status"] == "updated"
    assert body["id"] == first["id"]

    db.expire_all()
    recipe = (await db.execute(select(Recipe).where(Recipe.id == first["id"]))).scalar_one()
    assert recipe.recipe_data["notes"] == "Rinse the lentils first."
    count = (await db.execute(select(Recipe).where(Recipe.name == "Weeknight Dal"))).scalars().all()
    assert len(count) == 1


async def test_intake_update_creates_when_no_duplicate(client: AsyncClient, token_headers: dict):
    client.cookies.clear()
    response = await client.post(
        INTAKE_URL, params={"on_duplicate": "update"}, json=SIPHON_RECIPE, headers=token_headers
    )
    assert response.json()["status"] == "created"


async def test_intake_rejects_unknown_on_duplicate(client: AsyncClient, token_headers: dict):
    client.cookies.clear()
    response = await client.post(
        INTAKE_URL, params={"on_duplicate": "create"}, json=SIPHON_RECIPE, headers=token_headers
    )
    assert response.status_code == 422


async def test_intake_recipe_visible_to_session(
    client: AsyncClient, test_user_headers: dict, token_headers: dict
):
    created = (await client.post(INTAKE_URL, json=SIPHON_RECIPE, headers=token_headers)).json()

    response = await client.get(f"/api/v1/recipes/{created['id']}", headers=test_user_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Weeknight Dal"


async def test_intake_accepts_session_auth(client: AsyncClient, test_user_headers: dict):
    response = await client.post(INTAKE_URL, json=SIPHON_RECIPE, headers=test_user_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "created"


async def test_intake_missing_name_returns_error_envelope(
    client: AsyncClient, token_headers: dict, db: AsyncSession
):
    client.cookies.clear()
    response = await client.post(
        INTAKE_URL, json={"recipeIngredient": ["1 egg"]}, headers=token_headers
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error_code"] == "INVALID_INPUT"
    assert "name" in body["message"].lower()
    assert "details" in body
    assert (await db.execute(select(Recipe))).scalars().all() == []


async def test_intake_rejects_non_object_body(client: AsyncClient, token_headers: dict):
    client.cookies.clear()
    response = await client.post(INTAKE_URL, json=[SIPHON_RECIPE], headers=token_headers)
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


async def test_intake_requires_auth(client: AsyncClient):
    response = await client.post(INTAKE_URL, json=SIPHON_RECIPE)
    assert response.status_code == 401


async def test_intake_fetches_image_through_safe_fetch(
    client: AsyncClient, token_headers: dict, db: AsyncSession
):
    client.cookies.clear()
    payload = {**SIPHON_RECIPE, "image": "https://images.example.com/dal.jpg"}

    with patch("app.utils.recipe_format.safe_fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = FetchResult(
            url="https://images.example.com/dal.jpg", content=b"jpeg", content_type="image/jpeg"
        )
        body = (await client.post(INTAKE_URL, json=payload, headers=token_headers)).json()

    mock_fetch.assert_awaited_once()
    recipe = (await db.execute(select(Recipe).where(Recipe.id == body["id"]))).scalar_one()
    assert recipe.image_url == "https://images.example.com/dal.jpg"
    assert recipe.recipe_data["images"][0]["data"] == "anBlZw=="  # base64 of b"jpeg"


async def test_intake_private_image_url_saved_without_data(
    client: AsyncClient, token_headers: dict, db: AsyncSession
):
    client.cookies.clear()
    payload = {**SIPHON_RECIPE, "image": "http://169.254.169.254/latest/meta-data/"}

    body = (await client.post(INTAKE_URL, json=payload, headers=token_headers)).json()

    assert body["status"] == "created"
    recipe = (await db.execute(select(Recipe).where(Recipe.id == body["id"]))).scalar_one()
    assert recipe.recipe_data["images"] == [
        {"url": "http://169.254.169.254/latest/meta-data/", "data": "", "mimeType": "image/jpeg"}
    ]
