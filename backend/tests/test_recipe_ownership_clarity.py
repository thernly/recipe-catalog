"""What a household member can see and do with a recipe someone else added."""


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


async def _shared_recipe(client) -> tuple[dict[str, str], dict[str, str], dict]:
    """An owner and a member in one household, and a recipe the owner added."""
    owner = await _login(client, "owner@example.com")
    member = await _login(client, "member@example.com")
    household_id = (await client.get("/api/v1/households/me", headers=owner)).json()["id"]
    link = await client.post(
        f"/api/v1/households/{household_id}/invite-links", headers=owner, json={}
    )
    joined = await client.post(
        "/api/v1/households/join", headers=member, json={"code": link.json()["code"]}
    )
    assert joined.status_code == 200, joined.text
    recipe = await client.post(
        "/api/v1/recipes/",
        headers=owner,
        json={"name": "Owner stew", "recipe_data": {"recipeIngredient": ["1 onion"]}},
    )
    assert recipe.status_code == 201, recipe.text
    return owner, member, recipe.json()


async def test_recipe_list_says_who_added_each_recipe(client):
    owner, member, recipe = await _shared_recipe(client)

    listed = await client.get("/api/v1/recipes/search", headers=member)
    assert listed.status_code == 200, listed.text
    [summary] = listed.json()["recipes"]
    assert summary["user_id"] == recipe["user_id"]
    assert summary["creator_display_name"] == "owner"


async def test_member_can_copy_a_shared_recipe_into_their_own(client):
    owner, member, recipe = await _shared_recipe(client)
    member_id = (await client.get("/api/v1/users/me", headers=member)).json()["id"]

    copy = await client.post(f"/api/v1/recipes/{recipe['id']}/duplicate", headers=member)
    assert copy.status_code == 201, copy.text
    assert copy.json()["user_id"] == member_id
    assert copy.json()["name"] == "Owner stew (Copy)"

    # The copy is the member's to edit; the original still is not.
    url = "/api/v1/recipes/{}"
    mine = await client.patch(url.format(copy.json()["id"]), headers=member, json={"name": "Mine"})
    assert mine.status_code == 200, mine.text
    theirs = await client.patch(url.format(recipe["id"]), headers=member, json={"name": "Mine"})
    assert theirs.status_code == 404


async def test_other_households_cannot_copy_a_recipe(client):
    owner, member, recipe = await _shared_recipe(client)
    stranger = await _login(client, "stranger@example.com")

    copy = await client.post(f"/api/v1/recipes/{recipe['id']}/duplicate", headers=stranger)
    assert copy.status_code == 404


async def test_member_can_add_a_note_to_a_recipe_they_do_not_own(client):
    owner, member, recipe = await _shared_recipe(client)

    note = await client.post(
        f"/api/v1/recipes/{recipe['id']}/notes", headers=member, json={"text": "Needs more salt"}
    )
    assert note.status_code == 201, note.text
    seen = await client.get(f"/api/v1/recipes/{recipe['id']}/notes", headers=owner)
    assert [n["text"] for n in seen.json()] == ["Needs more salt"]
