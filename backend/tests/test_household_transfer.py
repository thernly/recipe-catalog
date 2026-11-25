"""Household ownership transfer (issue #433)."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services import household as household_service


async def _two_member_household(db: AsyncSession, owner: User):
    household = await household_service.create_household(db, "Shared", owner.id)
    member = User(
        email="member@example.com", hashed_password="hashed", is_active=True, is_verified=True
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    invitation = await household_service.create_invitation(
        db, household.id, owner.id, "member@example.com"
    )
    await household_service.accept_invitation(db, invitation.raw_token, member.id)
    return household, member


async def test_transfer_then_old_owner_can_leave(db: AsyncSession, test_user: User):
    household, member = await _two_member_household(db, test_user)

    updated = await household_service.transfer_ownership(db, household.id, member.id, test_user.id)

    assert updated.owner_user_id == member.id
    roles = {
        m.user_id: m.role for m in await household_service.get_household_members(db, household.id)
    }
    assert roles == {member.id: "owner", test_user.id: "member"}

    # The point of the issue: the former owner can now leave, and the household survives.
    result = await household_service.leave_household(db, test_user.id)
    assert result["household_deleted"] is False
    remaining = await household_service.get_household_members(db, household.id)
    assert [m.user_id for m in remaining] == [member.id]


async def test_only_owner_can_transfer(db: AsyncSession, test_user: User):
    household, member = await _two_member_household(db, test_user)

    with pytest.raises(HTTPException) as exc:
        await household_service.transfer_ownership(db, household.id, member.id, member.id)

    assert exc.value.status_code == 403
    await db.refresh(household)
    assert household.owner_user_id == test_user.id


async def test_cannot_transfer_to_non_member(db: AsyncSession, test_user: User):
    household, _ = await _two_member_household(db, test_user)
    outsider = User(
        email="outsider@example.com", hashed_password="hashed", is_active=True, is_verified=True
    )
    db.add(outsider)
    await db.commit()

    with pytest.raises(HTTPException) as exc:
        await household_service.transfer_ownership(db, household.id, outsider.id, test_user.id)

    assert exc.value.status_code == 404


async def test_transfer_route_is_wired(client, test_user_headers):
    household = (await client.get("/api/v1/households/me", headers=test_user_headers)).json()
    url = f"/api/v1/households/{household['id']}/transfer-ownership"

    to_self = await client.post(
        url, headers=test_user_headers, json={"new_owner_user_id": household["owner_user_id"]}
    )
    to_stranger = await client.post(
        url, headers=test_user_headers, json={"new_owner_user_id": 999999}
    )

    assert to_self.status_code == 400
    assert to_stranger.status_code == 404
