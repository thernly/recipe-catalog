"""Recipe notes: household members add them, authors edit, author or recipe owner deletes."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe_note import RecipeNote
from app.models.user import User


RECIPES = "/api/v1/recipes"


async def _login(
    client: AsyncClient, email: str, display_name: str | None = None
) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123!", "display_name": display_name},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "SecurePass123!"}
    )
    return {"Authorization": f"Bearer {response.cookies.get('access_token')}"}


async def _household(client: AsyncClient) -> tuple[dict[str, str], dict[str, str]]:
    """Owner and a member who share a household."""
    owner = await _login(client, "owner@example.com", "Olive")
    member = await _login(client, "member@example.com", "Milo")
    household_id = (await client.get("/api/v1/households/me", headers=owner)).json()["id"]
    invitation = await client.post(
        f"/api/v1/households/{household_id}/invitations",
        headers=owner,
        json={"invitee_email": "member@example.com"},
    )
    accepted = await client.post(
        "/api/v1/households/invitations/accept",
        headers=member,
        json={"token": invitation.json()["token"]},
    )
    assert accepted.status_code == 200, accepted.text
    return owner, member


async def _recipe(client: AsyncClient, headers: dict[str, str]) -> int:
    response = await client.post(
        f"{RECIPES}/",
        json={"name": "Soup", "recipe_data": {"recipeIngredient": ["1 cup stock"]}},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return int(response.json()["id"])


async def _add(client: AsyncClient, headers: dict[str, str], recipe_id: int, text: str) -> dict:
    response = await client.post(
        f"{RECIPES}/{recipe_id}/notes", json={"text": text}, headers=headers
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_household_members_add_and_list_notes(client: AsyncClient):
    owner, member = await _household(client)
    recipe_id = await _recipe(client, owner)

    first = await _add(client, owner, recipe_id, "Needs more salt")
    second = await _add(client, member, recipe_id, "Halved the sugar,\nstill sweet")

    listed = await client.get(f"{RECIPES}/{recipe_id}/notes", headers=owner)
    assert listed.status_code == 200
    notes = listed.json()
    # Newest first, author shown by display name, never by email
    assert [(n["id"], n["author_name"], n["is_author"]) for n in notes] == [
        (second["id"], "Milo", False),
        (first["id"], "Olive", True),
    ]
    assert notes[0]["text"] == "Halved the sugar,\nstill sweet"
    assert notes[0]["created_at"].endswith(("Z", "+00:00"))
    assert notes[0]["updated_at"] is None
    assert "@" not in listed.text


async def test_author_name_falls_back_to_email_prefix(client: AsyncClient):
    headers = await _login(client, "sam.cook@example.com")
    recipe_id = await _recipe(client, headers)

    note = await _add(client, headers, recipe_id, "Great")

    assert note["author_name"] == "sam.cook"


async def test_text_is_plain_and_required(client: AsyncClient):
    headers = await _login(client, "cook@example.com", "Cook")
    recipe_id = await _recipe(client, headers)

    note = await _add(client, headers, recipe_id, "<b>Crisp</b> & golden")
    assert note["text"] == "Crisp & golden"

    for text in ["", "   ", "<p></p>", "x" * 10001]:
        response = await client.post(
            f"{RECIPES}/{recipe_id}/notes", json={"text": text}, headers=headers
        )
        assert response.status_code == 422, text


async def test_only_author_edits(client: AsyncClient):
    owner, member = await _household(client)
    recipe_id = await _recipe(client, owner)
    note = await _add(client, member, recipe_id, "Too salty")
    url = f"{RECIPES}/{recipe_id}/notes/{note['id']}"

    # Not even the recipe's owner may rewrite someone else's note
    denied = await client.patch(url, json={"text": "Perfect"}, headers=owner)
    assert denied.status_code == 403

    edited = await client.patch(url, json={"text": "Too salty; use half"}, headers=member)
    assert edited.status_code == 200
    assert edited.json()["text"] == "Too salty; use half"
    assert edited.json()["updated_at"] is not None
    assert edited.json()["created_at"] == note["created_at"]


async def test_author_or_recipe_owner_deletes(client: AsyncClient):
    owner, member = await _household(client)
    recipe_id = await _recipe(client, owner)
    by_owner = await _add(client, owner, recipe_id, "Owner's note")
    by_member = await _add(client, member, recipe_id, "Member's note")
    by_member_2 = await _add(client, member, recipe_id, "Another")

    # A member cannot delete the owner's note on the owner's recipe
    denied = await client.delete(f"{RECIPES}/{recipe_id}/notes/{by_owner['id']}", headers=member)
    assert denied.status_code == 403
    # The recipe's owner can delete a member's note; the author can delete their own
    assert (
        await client.delete(f"{RECIPES}/{recipe_id}/notes/{by_member['id']}", headers=owner)
    ).status_code == 204
    assert (
        await client.delete(f"{RECIPES}/{recipe_id}/notes/{by_member_2['id']}", headers=member)
    ).status_code == 204

    remaining = (await client.get(f"{RECIPES}/{recipe_id}/notes", headers=owner)).json()
    assert [n["id"] for n in remaining] == [by_owner["id"]]


async def test_other_household_gets_404(client: AsyncClient):
    owner = await _login(client, "owner@example.com", "Olive")
    stranger = await _login(client, "stranger@example.com", "Stan")
    recipe_id = await _recipe(client, owner)
    note = await _add(client, owner, recipe_id, "Ours")
    note_url = f"{RECIPES}/{recipe_id}/notes/{note['id']}"

    responses = [
        await client.get(f"{RECIPES}/{recipe_id}/notes", headers=stranger),
        await client.post(f"{RECIPES}/{recipe_id}/notes", json={"text": "Hi"}, headers=stranger),
        await client.patch(note_url, json={"text": "Mine"}, headers=stranger),
        await client.delete(note_url, headers=stranger),
    ]
    for response in responses:
        assert response.status_code == 404, response.request.url

    # A note id under the wrong recipe is a 404 too
    other_recipe = await _recipe(client, owner)
    wrong = await client.delete(f"{RECIPES}/{other_recipe}/notes/{note['id']}", headers=owner)
    assert wrong.status_code == 404


async def test_notes_survive_recipe_edit(client: AsyncClient):
    headers = await _login(client, "cook@example.com", "Cook")
    recipe_id = await _recipe(client, headers)
    note = await _add(client, headers, recipe_id, "Keep me")

    updated = await client.patch(
        f"{RECIPES}/{recipe_id}",
        json={"name": "Better soup", "recipe_data": {"recipeIngredient": ["2 cups stock"]}},
        headers=headers,
    )
    assert updated.status_code == 200

    notes = (await client.get(f"{RECIPES}/{recipe_id}/notes", headers=headers)).json()
    assert [(n["id"], n["text"]) for n in notes] == [(note["id"], "Keep me")]


async def test_trash_hides_notes_and_restore_brings_them_back(client: AsyncClient):
    headers = await _login(client, "cook@example.com", "Cook")
    recipe_id = await _recipe(client, headers)
    await _add(client, headers, recipe_id, "Keep me")

    assert (await client.delete(f"{RECIPES}/{recipe_id}", headers=headers)).status_code == 204
    trashed = await client.get(f"{RECIPES}/{recipe_id}/notes", headers=headers)
    assert trashed.status_code == 404

    assert (await client.post(f"{RECIPES}/{recipe_id}/restore", headers=headers)).status_code == 200
    restored = (await client.get(f"{RECIPES}/{recipe_id}/notes", headers=headers)).json()
    assert [n["text"] for n in restored] == ["Keep me"]


async def test_permanent_delete_removes_notes(client: AsyncClient, test_db: AsyncSession):
    headers = await _login(client, "cook@example.com", "Cook")
    recipe_id = await _recipe(client, headers)
    await _add(client, headers, recipe_id, "Gone with the recipe")

    deleted = await client.delete(f"{RECIPES}/{recipe_id}?permanent=true", headers=headers)
    assert deleted.status_code == 204

    rows = (await test_db.execute(select(RecipeNote))).scalars().all()
    assert rows == []


async def test_account_deletion_removes_that_users_notes(
    client: AsyncClient, test_db: AsyncSession
):
    owner, member = await _household(client)
    recipe_id = await _recipe(client, owner)
    await _add(client, owner, recipe_id, "Owner's note")
    await _add(client, member, recipe_id, "Member's note")

    assert (await client.delete("/api/v1/users/me", headers=member)).status_code == 200

    texts = [
        n["text"] for n in (await client.get(f"{RECIPES}/{recipe_id}/notes", headers=owner)).json()
    ]
    assert texts == ["Owner's note"]
    remaining_users = (await test_db.execute(select(User.email))).scalars().all()
    assert "member@example.com" not in remaining_users
