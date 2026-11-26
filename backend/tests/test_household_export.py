"""Exports can cover the whole household's recipes, not only the caller's own."""

from io import BytesIO

import pytest
from httpx import AsyncClient

from tests.test_recipe_notes import RECIPES, _household, _login, _recipe


async def _two_cooks(client: AsyncClient) -> tuple[dict[str, str], dict[str, str]]:
    """Olive owns "Soup"; Milo, in the same household, owns "Bread"."""
    owner, member = await _household(client)
    await _recipe(client, owner)
    await _named(client, member, "Bread")
    return owner, member


async def _named(client: AsyncClient, headers: dict[str, str], name: str) -> int:
    response = await client.post(
        f"{RECIPES}/", json={"name": name, "recipe_data": {}}, headers=headers
    )
    assert response.status_code == 201, response.text
    return int(response.json()["id"])


@pytest.mark.parametrize("fmt", ["json", "markdown", "text"])
async def test_recipe_export_defaults_to_own_and_can_cover_household(client: AsyncClient, fmt: str):
    owner, _ = await _two_cooks(client)

    own = (await client.get(f"/api/v1/export/recipes?format={fmt}", headers=owner)).text
    assert "soup" in own.lower() and "bread" not in own.lower()

    response = await client.get(
        f"/api/v1/export/recipes?format={fmt}&scope=household", headers=owner
    )
    assert response.status_code == 200, response.text
    assert "soup" in response.text.lower() and "bread" in response.text.lower()


async def test_backup_can_cover_household_recipes(client: AsyncClient):
    owner, _ = await _two_cooks(client)

    own = (await client.get("/api/v1/export/all", headers=owner)).json()
    assert [r["name"] for r in own["recipes"]] == ["Soup"]

    backup = (await client.get("/api/v1/export/all?scope=household", headers=owner)).json()
    assert sorted(r["name"] for r in backup["recipes"]) == ["Bread", "Soup"]
    assert backup["statistics"]["total_recipes"] == 2


async def test_household_export_excludes_other_households_and_trash(client: AsyncClient):
    owner, member = await _two_cooks(client)
    stranger = await _login(client, "stranger@example.com", "Sam")
    await _named(client, stranger, "Pie")
    stew_id = await _named(client, member, "Stew")
    deleted = await client.delete(f"{RECIPES}/{stew_id}", headers=member)
    assert deleted.status_code == 204, deleted.text

    exported = (
        await client.get("/api/v1/export/recipes?format=json&scope=household", headers=owner)
    ).json()

    assert sorted(r["name"] for r in exported) == ["Bread", "Soup"]


async def test_restoring_a_household_backup_does_not_copy_housemates_recipes(client: AsyncClient):
    owner, member = await _two_cooks(client)
    backup = (await client.get("/api/v1/export/all?scope=household", headers=owner)).content

    response = await client.post(
        "/api/v1/import/backup",
        files={"file": ("backup.json", BytesIO(backup), "application/json")},
        headers=owner,
    )

    assert response.status_code == 200, response.text
    details = response.json()["details"]
    assert (details["created"], details["skipped"]) == (0, 2)
    listed = (await client.get(f"{RECIPES}/search", headers=member)).json()
    assert sorted(r["name"] for r in listed["recipes"]) == ["Bread", "Soup"]


async def test_export_rejects_an_unknown_scope(client: AsyncClient):
    owner = await _login(client, "owner@example.com", "Olive")

    response = await client.get("/api/v1/export/recipes?scope=everyone", headers=owner)

    assert response.status_code == 422
