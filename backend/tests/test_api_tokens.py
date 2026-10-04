"""Tests for personal API token management."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import API_TOKEN_PREFIX, MAX_API_TOKENS_PER_USER
from app.core.security import hash_token
from app.models.api_token import ApiToken


TOKENS_URL = "/api/v1/users/me/api-tokens"


async def register_and_login(client: AsyncClient, email: str) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123!", "display_name": "Other"},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "SecurePass123!"}
    )
    return {"Authorization": f"Bearer {response.cookies.get('access_token')}"}


async def test_create_token_returns_value_once(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    response = await client.post(
        TOKENS_URL, json={"name": "Firefox laptop"}, headers=test_user_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Firefox laptop"
    assert body["token"].startswith(API_TOKEN_PREFIX)
    assert body["token"].startswith(body["token_prefix"])
    assert body["last_used_at"] is None

    # Only the hash is stored
    row = (await db.execute(select(ApiToken).where(ApiToken.id == body["id"]))).scalar_one()
    assert row.token_hash == hash_token(body["token"])
    assert body["token"] not in (row.token_hash, row.token_prefix)

    # Listing never returns the token value
    listed = (await client.get(TOKENS_URL, headers=test_user_headers)).json()
    assert [t["id"] for t in listed] == [body["id"]]
    assert "token" not in listed[0]


async def test_create_token_rejects_blank_name(client: AsyncClient, test_user_headers: dict):
    for name in ["", "   "]:
        response = await client.post(TOKENS_URL, json={"name": name}, headers=test_user_headers)
        assert response.status_code == 422


async def test_create_token_strips_html_from_name(client: AsyncClient, test_user_headers: dict):
    response = await client.post(
        TOKENS_URL, json={"name": "<b>Chrome</b>"}, headers=test_user_headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Chrome"


async def test_active_token_limit(client: AsyncClient, test_user_headers: dict):
    ids = []
    for i in range(MAX_API_TOKENS_PER_USER):
        response = await client.post(TOKENS_URL, json={"name": f"t{i}"}, headers=test_user_headers)
        assert response.status_code == 201
        ids.append(response.json()["id"])

    response = await client.post(TOKENS_URL, json={"name": "one more"}, headers=test_user_headers)
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_INPUT"

    # Revoking one frees a slot
    await client.delete(f"{TOKENS_URL}/{ids[0]}", headers=test_user_headers)
    response = await client.post(TOKENS_URL, json={"name": "one more"}, headers=test_user_headers)
    assert response.status_code == 201


async def test_revoke_token(client: AsyncClient, test_user_headers: dict, db: AsyncSession):
    created = (
        await client.post(TOKENS_URL, json={"name": "Old browser"}, headers=test_user_headers)
    ).json()

    response = await client.delete(f"{TOKENS_URL}/{created['id']}", headers=test_user_headers)
    assert response.status_code == 204

    assert (await client.get(TOKENS_URL, headers=test_user_headers)).json() == []
    row = (await db.execute(select(ApiToken).where(ApiToken.id == created["id"]))).scalar_one()
    assert row.revoked_at is not None

    # A second revoke finds nothing
    response = await client.delete(f"{TOKENS_URL}/{created['id']}", headers=test_user_headers)
    assert response.status_code == 404


async def test_tokens_are_per_user(client: AsyncClient, test_user_headers: dict):
    mine = (await client.post(TOKENS_URL, json={"name": "Mine"}, headers=test_user_headers)).json()

    other_headers = await register_and_login(client, "other@example.com")
    assert (await client.get(TOKENS_URL, headers=other_headers)).json() == []

    # Another user cannot revoke it
    response = await client.delete(f"{TOKENS_URL}/{mine['id']}", headers=other_headers)
    assert response.status_code == 404
    listed = (await client.get(TOKENS_URL, headers=test_user_headers)).json()
    assert [t["id"] for t in listed] == [mine["id"]]


async def test_token_management_requires_session(client: AsyncClient, test_user_headers: dict):
    token = (
        await client.post(TOKENS_URL, json={"name": "Siphon"}, headers=test_user_headers)
    ).json()["token"]
    client.cookies.clear()

    assert (await client.get(TOKENS_URL)).status_code == 401
    # An API token cannot be used to manage tokens
    token_headers = {"Authorization": f"Bearer {token}"}
    assert (await client.get(TOKENS_URL, headers=token_headers)).status_code == 401
    assert (
        await client.post(TOKENS_URL, json={"name": "x"}, headers=token_headers)
    ).status_code == 401


async def test_api_token_rejected_outside_intake(client: AsyncClient, test_user_headers: dict):
    token = (
        await client.post(TOKENS_URL, json={"name": "Siphon"}, headers=test_user_headers)
    ).json()["token"]
    client.cookies.clear()
    token_headers = {"Authorization": f"Bearer {token}"}

    assert (await client.get("/api/v1/users/me", headers=token_headers)).status_code == 401
    response = await client.post(
        "/api/v1/import/recipes/json", json=[{"name": "Sneaky"}], headers=token_headers
    )
    assert response.status_code == 401
