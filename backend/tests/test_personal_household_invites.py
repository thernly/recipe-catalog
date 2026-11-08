"""Newly registered users can accept an invitation to another household."""

import importlib.util
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select, text

from app.models._utils import utc_now
from app.models.household import Household, HouseholdInvitation, HouseholdMember
from app.models.user import User


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


async def test_new_user_can_accept_invitation(client):
    owner = await _login(client, "owner@example.com")
    invitee = await _login(client, "invitee@example.com")

    recipe = await client.post(
        "/api/v1/recipes/", headers=invitee, json={"name": "Invitee soup", "recipe_data": {}}
    )
    assert recipe.status_code == 201

    household_id = (await client.get("/api/v1/households/me", headers=owner)).json()["id"]
    old_household_id = (await client.get("/api/v1/households/me", headers=invitee)).json()["id"]
    invitation = await client.post(
        f"/api/v1/households/{household_id}/invitations",
        headers=owner,
        json={"invitee_email": "invitee@example.com"},
    )
    assert invitation.status_code == 201, invitation.text

    accepted = await client.post(
        "/api/v1/households/invitations/accept",
        headers=invitee,
        json={"token": invitation.json()["token"]},
    )
    assert accepted.status_code == 200, accepted.text

    me = (await client.get("/api/v1/households/me", headers=invitee)).json()
    assert me["id"] == household_id
    # The invitee's recipe followed them and is visible to the owner.
    found = await client.get(f"/api/v1/recipes/{recipe.json()['id']}", headers=owner)
    assert found.status_code == 200
    # Their now-empty registration household was removed.
    gone = await client.get(f"/api/v1/households/{old_household_id}/members", headers=invitee)
    assert gone.status_code in (403, 404)


async def test_solo_households_personal_migration(test_db, monkeypatch):
    path = Path(__file__).parents[1] / "alembic/versions/20261107_solo_households_personal.py"
    spec = importlib.util.spec_from_file_location("solo_personal", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    statements: list[str] = []
    monkeypatch.setattr(migration.op, "execute", statements.append, raising=False)
    migration.upgrade()
    assert len(statements) == 1

    users = [User(email=f"u{i}@example.com") for i in range(4)]
    test_db.add_all(users)
    await test_db.flush()

    def household(owner: User, name: str) -> Household:
        h = Household(name=name, owner_user_id=owner.id, is_personal=False)
        test_db.add(h)
        return h

    solo = household(users[0], "solo")
    invited = household(users[1], "pending invite")
    shared = household(users[2], "shared")
    await test_db.flush()
    test_db.add_all(
        [
            HouseholdMember(household_id=solo.id, user_id=users[0].id, role="owner"),
            HouseholdMember(household_id=invited.id, user_id=users[1].id, role="owner"),
            HouseholdMember(household_id=shared.id, user_id=users[2].id, role="owner"),
            HouseholdMember(household_id=shared.id, user_id=users[3].id, role="member"),
            HouseholdInvitation(
                household_id=invited.id,
                inviter_user_id=users[1].id,
                invitee_email="someone@example.com",
                token="hashed-token",
                expires_at=utc_now() + timedelta(days=3),
            ),
        ]
    )
    await test_db.commit()

    await test_db.execute(text(statements[0]))
    await test_db.commit()

    rows = dict((await test_db.execute(select(Household.name, Household.is_personal))).all())
    assert rows == {"solo": True, "pending invite": False, "shared": False}
