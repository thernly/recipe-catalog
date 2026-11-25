"""Putting household recipes into your own collections, and asking where a recipe is."""


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


async def _favorites_id(client, headers) -> int:
    me = (await client.get("/api/v1/users/me", headers=headers)).json()["id"]
    collections = (await client.get("/api/v1/collections/", headers=headers)).json()
    return next(c["id"] for c in collections if c["is_default"] and c["user_id"] == me)


async def _recipe_id(client, headers, name: str) -> int:
    recipe = await client.post(
        "/api/v1/recipes/", headers=headers, json={"name": name, "recipe_data": {}}
    )
    assert recipe.status_code == 201, recipe.text
    return recipe.json()["id"]


async def test_member_can_favorite_a_recipe_another_member_added(client):
    owner = await _login(client, "owner@example.com")
    member = await _login(client, "member@example.com")
    household_id = (await client.get("/api/v1/households/me", headers=owner)).json()["id"]
    link = await client.post(
        f"/api/v1/households/{household_id}/invite-links", headers=owner, json={}
    )
    await client.post("/api/v1/households/join", headers=member, json={"code": link.json()["code"]})
    shared = await _recipe_id(client, owner, "Owner stew")
    favorites = await _favorites_id(client, member)

    added = await client.post(
        f"/api/v1/collections/{favorites}/recipes", headers=member, json={"recipe_ids": [shared]}
    )
    assert added.status_code == 200, added.text
    assert added.json()["added"] == [shared]

    containing = await client.get(f"/api/v1/collections/containing/{shared}", headers=member)
    assert containing.status_code == 200, containing.text
    assert containing.json() == [favorites]
    # The owner's own collections are a separate matter.
    theirs = await client.get(f"/api/v1/collections/containing/{shared}", headers=owner)
    assert theirs.json() == []


async def test_recipe_from_another_household_cannot_be_added(client):
    me = await _login(client, "me@example.com")
    stranger = await _login(client, "stranger@example.com")
    foreign = await _recipe_id(client, stranger, "Secret soup")
    favorites = await _favorites_id(client, me)

    added = await client.post(
        f"/api/v1/collections/{favorites}/recipes", headers=me, json={"recipe_ids": [foreign]}
    )
    assert added.status_code == 200, added.text
    assert added.json()["added"] == []
    assert added.json()["not_found"] == [foreign]
