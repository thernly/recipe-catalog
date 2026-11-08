"""Import/intake tolerate odd fields, and reads tolerate any stored value."""

import pytest
from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe
from app.models.user import User
from app.utils import recipe_format


IMPORT = "/api/v1/import/recipes/json"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def fake_fetch(url):
        return None

    monkeypatch.setattr(recipe_format, "_fetch_and_encode_image", fake_fetch)


async def _import(client, headers, recipes, handling="create"):
    resp = await client.post(
        f"{IMPORT}?duplicate_handling={handling}", json=recipes, headers=headers
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["details"]


async def _reads_ok(client, headers, recipe_id):
    assert (await client.get("/api/v1/recipes/search", headers=headers)).status_code == 200
    assert (await client.get(f"/api/v1/recipes/{recipe_id}", headers=headers)).status_code == 200
    resp = await client.patch(
        f"/api/v1/recipes/{recipe_id}", json={"cuisine": "Thai"}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_long_description_import_then_reads(client: AsyncClient, auth_headers):
    details = await _import(client, auth_headers, [{"name": "Long", "description": "x" * 11000}])
    assert details["created"] == 1
    body = await _reads_ok(client, auth_headers, details["items"][0]["recipe_id"])
    assert len(body["description"]) == 10000


async def test_legacy_row_reads(
    client: AsyncClient, auth_headers, db: AsyncSession, test_user: User, test_household
):
    recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household["id"],
        name="Legacy",
        description="y" * 20000,
        source_url="javascript:alert(1)",
        image_url="data:image/png;base64,AAAA",
        recipe_data={},
        source_type="manual",
    )
    db.add(recipe)
    await db.commit()
    body = await _reads_ok(client, auth_headers, recipe.id)
    assert body["source_url"] is None and body["image_url"] is None
    search = (await client.get("/api/v1/recipes/search", headers=auth_headers)).json()
    assert search["recipes"][0]["image_url"] is None


async def test_ampersand_kept_and_duplicate_matched(client: AsyncClient, auth_headers, db):
    details = await _import(client, auth_headers, [{"name": "Mac & Cheese <b>x</b>"}])
    rid = details["items"][0]["recipe_id"]
    stored = (await db.execute(select(Recipe.name).where(Recipe.id == rid))).scalar_one()
    assert stored == "Mac & Cheese x"
    again = await _import(client, auth_headers, [{"name": "Mac & Cheese <b>x</b>"}], "skip")
    assert again["skipped"] == 1 and again["items"][0]["recipe_id"] == rid


async def test_bad_fields_dropped_not_rejected(client: AsyncClient, auth_headers, db):
    images = [f"https://cdn.example.com/{i}.jpg" for i in range(7)]
    images[0] = "//cdn.example.com/rel.jpg"
    images.insert(1, {"data": "AAAA", "mimeType": "image/gif"})
    images.insert(2, {"url": "https://cdn.example.com/a.gif", "mimeType": "image/gif"})
    details = await _import(
        client, auth_headers, [{"name": "Tolerant", "url": "www.x.com", "image": images}]
    )
    assert details["created"] == 1 and details["failed"] == 0
    recipe = (
        await db.execute(select(Recipe).where(Recipe.id == details["items"][0]["recipe_id"]))
    ).scalar_one()
    assert recipe.source_url is None
    urls = [img["url"] for img in recipe.recipe_data["images"]]
    assert len(urls) == 5
    assert urls[0] == "https://cdn.example.com/a.gif"
    assert all(u.startswith("https://") for u in urls)
    assert recipe.image_url == urls[0]
