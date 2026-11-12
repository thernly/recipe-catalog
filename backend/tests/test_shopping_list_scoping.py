"""Shopping lists through the API: other households get 404, household members share."""

from httpx import AsyncClient


BASE = "/api/v1/shopping-lists"


async def _login(client: AsyncClient, email: str) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123!", "display_name": email},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "SecurePass123!"}
    )
    return {"Authorization": f"Bearer {response.cookies.get('access_token')}"}


async def _list_with_item(client: AsyncClient, headers: dict[str, str]) -> tuple[int, int]:
    created = await client.post(f"{BASE}/", json={"name": "Groceries"}, headers=headers)
    list_id = created.json()["id"]
    item = await client.post(f"{BASE}/{list_id}/items", json={"item_name": "milk"}, headers=headers)
    return list_id, item.json()["id"]


async def test_other_household_cannot_touch_list_or_items(client: AsyncClient):
    owner = await _login(client, "owner@example.com")
    stranger = await _login(client, "stranger@example.com")
    list_id, item_id = await _list_with_item(client, owner)

    responses = [
        await client.get(f"{BASE}/{list_id}", headers=stranger),
        await client.patch(f"{BASE}/{list_id}", json={"name": "Mine"}, headers=stranger),
        await client.post(f"{BASE}/{list_id}/archive", headers=stranger),
        await client.post(f"{BASE}/{list_id}/duplicate", headers=stranger),
        await client.patch(f"{BASE}/items/{item_id}", json={"checked": True}, headers=stranger),
        await client.delete(f"{BASE}/items/{item_id}", headers=stranger),
        await client.delete(f"{BASE}/{list_id}", headers=stranger),
    ]
    for res in responses:
        assert res.status_code == 404, res.request.url

    assert all(
        lst["id"] != list_id for lst in (await client.get(f"{BASE}/", headers=stranger)).json()
    )
    # Untouched for the owner.
    detail = (await client.get(f"{BASE}/{list_id}", headers=owner)).json()
    assert detail["name"] == "Groceries"
    assert [(i["id"], i["checked"]) for i in detail["items"]] == [(item_id, False)]


async def test_household_member_can_edit_and_delete(client: AsyncClient):
    owner = await _login(client, "owner@example.com")
    member = await _login(client, "member@example.com")
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
    list_id, item_id = await _list_with_item(client, owner)

    checked = await client.patch(f"{BASE}/items/{item_id}", json={"checked": True}, headers=member)
    assert checked.status_code == 200
    renamed = await client.patch(f"{BASE}/{list_id}", json={"name": "Ours"}, headers=member)
    assert renamed.status_code == 200
    assert (await client.delete(f"{BASE}/items/{item_id}", headers=member)).status_code == 204
    assert (await client.delete(f"{BASE}/{list_id}", headers=member)).status_code == 204
    assert (await client.get(f"{BASE}/{list_id}", headers=owner)).status_code == 404
