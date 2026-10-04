"""Tests for the CSRF middleware, including the skip for personal-API-token requests.

conftest forces ENVIRONMENT=testing, which turns the CSRF check off; these tests switch
it back on.
"""

import pytest
from httpx import AsyncClient
from starlette.requests import Request

from app.core.config import settings
from app.middleware.csrf import is_api_token_request


RECIPE = {"name": "CSRF Soup", "recipeIngredient": ["water"]}


@pytest.fixture
def csrf_enabled(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")


@pytest.fixture
async def api_token(client: AsyncClient, test_user_headers: dict) -> str:
    response = await client.post(
        "/api/v1/users/me/api-tokens", json={"name": "Siphon"}, headers=test_user_headers
    )
    return response.json()["token"]


async def test_token_request_to_intake_skips_csrf(
    client: AsyncClient, api_token: str, csrf_enabled
):
    client.cookies.clear()
    response = await client.post(
        "/api/v1/intake", json=RECIPE, headers={"Authorization": f"Bearer {api_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "created"


async def test_cookie_request_to_intake_still_needs_csrf(
    client: AsyncClient, test_user_headers: dict, csrf_enabled
):
    # Cookies only (session from login), no CSRF header
    response = await client.post("/api/v1/intake", json=RECIPE)
    assert response.status_code == 403
    assert response.json()["error_code"] == "csrf_token_invalid"

    # With the CSRF header it goes through
    response = await client.post(
        "/api/v1/intake",
        json=RECIPE,
        headers={"X-CSRF-Token": test_user_headers["X-CSRF-Token"]},
    )
    assert response.status_code == 200


async def test_token_header_does_not_skip_csrf_elsewhere(
    client: AsyncClient, api_token: str, csrf_enabled
):
    response = await client.post(
        "/api/v1/import/recipes/json",
        json=[RECIPE],
        headers={"Authorization": f"Bearer {api_token}"},
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == "csrf_token_invalid"


async def test_jwt_bearer_to_intake_still_needs_csrf(
    client: AsyncClient, test_user_headers: dict, csrf_enabled
):
    response = await client.post(
        "/api/v1/intake",
        json=RECIPE,
        headers={"Authorization": test_user_headers["Authorization"]},
    )
    assert response.status_code == 403


def make_request(path: str, authorization: str | None) -> Request:
    headers = [(b"authorization", authorization.encode())] if authorization else []
    return Request({"type": "http", "method": "POST", "path": path, "headers": headers})


@pytest.mark.parametrize(
    ("path", "authorization", "expected"),
    [
        ("/api/v1/intake", "Bearer rcat_abc", True),
        ("/api/v1/intake/check", "Bearer rcat_abc", True),
        ("/api/v1/intake", None, False),
        ("/api/v1/intake", "Bearer eyJhbGciOi", False),
        ("/api/v1/intake", "Basic rcat_abc", False),
        ("/api/v1/intakeother", "Bearer rcat_abc", False),
        ("/api/v1/recipes", "Bearer rcat_abc", False),
    ],
)
def test_is_api_token_request(path, authorization, expected):
    assert is_api_token_request(make_request(path, authorization)) is expected
