"""Revoking an invitation, and switching households by invite code."""


async def _login(client, email: str) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123!", "display_name": email},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "SecurePass123!"}
    )
    headers = {"Authorization": f"Bearer {response.cookies.get('access_token')}"}
    if csrf := response.cookies.get("csrf_token"):
        headers["X-CSRF-Token"] = csrf
    return headers


async def _household_id(client, headers) -> int:
    return (await client.get("/api/v1/households/me", headers=headers)).json()["id"]


async def _invite_code(client, headers) -> str:
    household_id = await _household_id(client, headers)
    link = await client.post(
        f"/api/v1/households/{household_id}/invite-links", headers=headers, json={}
    )
    assert link.status_code == 201, link.text
    return link.json()["code"]


async def test_owner_can_revoke_pending_invitation(client):
    owner = await _login(client, "owner@example.com")
    household_id = await _household_id(client, owner)
    invitation = await client.post(
        f"/api/v1/households/{household_id}/invitations",
        headers=owner,
        json={"invitee_email": "wrong@example.com"},
    )
    assert invitation.status_code == 201, invitation.text
    url = f"/api/v1/households/{household_id}/invitations/{invitation.json()['id']}"

    stranger = await _login(client, "stranger@example.com")
    assert (await client.delete(url, headers=stranger)).status_code == 403

    assert (await client.delete(url, headers=owner)).status_code == 204
    pending = await client.get(f"/api/v1/households/{household_id}/invitations", headers=owner)
    assert pending.json() == []
    assert (await client.delete(url, headers=owner)).status_code == 404


async def test_switching_household_with_a_bad_code_keeps_current_household(client):
    owner = await _login(client, "owner@example.com")
    member = await _login(client, "member@example.com")
    joined = await client.post(
        "/api/v1/households/join", headers=member, json={"code": await _invite_code(client, owner)}
    )
    assert joined.status_code == 200, joined.text
    shared_id = await _household_id(client, owner)

    failed = await client.post(
        "/api/v1/households/join",
        headers=member,
        json={"code": "no-such-code", "leave_current": True},
    )
    assert failed.status_code == 404
    assert await _household_id(client, member) == shared_id


async def test_switching_household_with_a_valid_code(client):
    first = await _login(client, "first@example.com")
    second = await _login(client, "second@example.com")
    member = await _login(client, "member@example.com")
    recipe = await client.post(
        "/api/v1/recipes/", headers=member, json={"name": "Member soup", "recipe_data": {}}
    )
    assert recipe.status_code == 201
    await client.post(
        "/api/v1/households/join", headers=member, json={"code": await _invite_code(client, first)}
    )
    code = await _invite_code(client, second)

    # Without leave_current the member is told to leave first, as before.
    refused = await client.post("/api/v1/households/join", headers=member, json={"code": code})
    assert refused.status_code == 400

    switched = await client.post(
        "/api/v1/households/join", headers=member, json={"code": code, "leave_current": True}
    )
    assert switched.status_code == 200, switched.text
    assert await _household_id(client, member) == await _household_id(client, second)
    # The member's recipe moved with them.
    url = f"/api/v1/recipes/{recipe.json()['id']}"
    assert (await client.get(url, headers=second)).status_code == 200
    assert (await client.get(url, headers=first)).status_code == 404
