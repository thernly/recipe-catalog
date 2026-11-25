"""A household member can open another member's collection, and counts skip trashed recipes."""

from datetime import UTC, datetime

from app.models.recipe import Recipe


async def _login(client, email: str) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123!", "display_name": email.split("@")[0]},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "SecurePass123!"}
    )
    headers = {"Authorization": f"Bearer {response.cookies.get('access_token')}"}
    if csrf := response.cookies.get("csrf_token"):
        headers["X-CSRF-Token"] = csrf
    return headers


async def _collection_with_two_recipes(client, owner) -> tuple[int, list[int]]:
    created = await client.post("/api/v1/collections/", headers=owner, json={"name": "Weeknight"})
    assert created.status_code == 201, created.text
    ids = []
    for name in ("Kept", "Trashed"):
        recipe = await client.post(
            "/api/v1/recipes/", headers=owner, json={"name": name, "recipe_data": {}}
        )
        ids.append(recipe.json()["id"])
    added = await client.post(
        f"/api/v1/collections/{created.json()['id']}/recipes",
        headers=owner,
        json={"recipe_ids": ids},
    )
    assert added.status_code == 200, added.text
    return created.json()["id"], ids


async def test_member_can_open_another_members_collection(client):
    owner = await _login(client, "owner@example.com")
    member = await _login(client, "member@example.com")
    stranger = await _login(client, "stranger@example.com")
    household_id = (await client.get("/api/v1/households/me", headers=owner)).json()["id"]
    link = await client.post(
        f"/api/v1/households/{household_id}/invite-links", headers=owner, json={}
    )
    await client.post("/api/v1/households/join", headers=member, json={"code": link.json()["code"]})
    collection_id, recipe_ids = await _collection_with_two_recipes(client, owner)
    url = f"/api/v1/collections/{collection_id}/recipes"

    seen = await client.get(url, headers=member)
    assert seen.status_code == 200, seen.text
    assert {r["name"] for r in seen.json()} == {"Kept", "Trashed"}
    # Looking is all a member may do; the collection is still the owner's to change.
    changed = await client.post(url, headers=member, json={"recipe_ids": recipe_ids})
    assert changed.status_code == 404
    assert (await client.get(url, headers=stranger)).status_code == 404


async def test_collection_counts_skip_trashed_recipes(client, test_db):
    owner = await _login(client, "owner@example.com")
    collection_id, ids = await _collection_with_two_recipes(client, owner)
    trashed = await test_db.get(Recipe, ids[1])
    trashed.deleted_at = datetime.now(UTC)
    await test_db.commit()

    listed = (await client.get("/api/v1/collections/", headers=owner)).json()
    assert next(c["recipe_count"] for c in listed if c["id"] == collection_id) == 1
    one = (await client.get(f"/api/v1/collections/{collection_id}", headers=owner)).json()
    assert one["recipe_count"] == 1
