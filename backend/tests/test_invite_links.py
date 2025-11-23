"""Tests for household invite links."""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import household as household_service


@pytest.mark.asyncio
async def test_create_invite_link(client: AsyncClient, test_user_headers: dict, test_household: dict):
    """Test creating an invite link."""
    response = await client.post(
        f"/api/households/{test_household['id']}/invite-links",
        headers=test_user_headers,
        json={"expires_in_days": 7},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "code" in data
    assert "-" in data["code"]  # Should be word-word-word format
    assert len(data["code"].split("-")) == 3  # Three words
    assert data["household_id"] == test_household["id"]
    assert data["used_at"] is None


@pytest.mark.asyncio
async def test_invite_code_format(db: AsyncSession, test_user: dict, test_household: dict):
    """Test that invite codes use word-based format."""
    invite_link = await household_service.create_invite_link(db, test_household["id"], test_user["id"], 7)

    # Should be three words separated by hyphens
    words = invite_link.code.split("-")
    assert len(words) == 3
    # Each word should be lowercase alphabetic
    for word in words:
        assert word.islower()
        assert word.isalpha()


@pytest.mark.asyncio
async def test_get_invite_link_info(client: AsyncClient, test_user_headers: dict, test_household: dict):
    """Test getting invite link information."""
    # Create invite link
    create_response = await client.post(
        f"/api/households/{test_household['id']}/invite-links",
        headers=test_user_headers,
        json={"expires_in_days": 7},
    )
    code = create_response.json()["code"]

    # Get info (public endpoint)
    response = await client.get(f"/api/households/join/{code}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["code"] == code
    assert data["household_name"] == test_household["name"]
    assert data["used_at"] is None


@pytest.mark.asyncio
async def test_join_via_invite_code(
    client: AsyncClient,
    test_user_headers: dict,
    test_household: dict,
    db: AsyncSession,
):
    """Test joining a household via invite code."""
    # Create a second user who will join
    register_response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "display_name": "New User",
        },
    )
    assert register_response.status_code == status.HTTP_201_CREATED

    # Login as new user
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "newuser@example.com", "password": "SecurePass123!"},
    )
    new_user_token = login_response.json()["access_token"]
    new_user_headers = {"Authorization": f"Bearer {new_user_token}"}

    # First, new user needs to leave their auto-created household
    leave_response = await client.post("/api/households/leave", headers=new_user_headers)
    assert leave_response.status_code == status.HTTP_200_OK

    # Create invite link from original household
    create_response = await client.post(
        f"/api/households/{test_household['id']}/invite-links",
        headers=test_user_headers,
        json={"expires_in_days": 7},
    )
    code = create_response.json()["code"]

    # New user joins via code
    join_response = await client.post(
        "/api/households/join",
        headers=new_user_headers,
        json={"code": code},
    )

    assert join_response.status_code == status.HTTP_200_OK
    data = join_response.json()
    assert data["household_id"] == test_household["id"]
    assert data["role"] == "member"
    assert data["user_email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_invite_code_one_time_use(
    client: AsyncClient,
    test_user_headers: dict,
    test_household: dict,
):
    """Test that invite codes can only be used once."""
    # Create two users
    await client.post(
        "/api/auth/register",
        json={
            "email": "user1@example.com",
            "password": "SecurePass123!",
            "display_name": "User 1",
        },
    )
    await client.post(
        "/api/auth/register",
        json={
            "email": "user2@example.com",
            "password": "SecurePass123!",
            "display_name": "User 2",
        },
    )

    # Login as user1
    login1 = await client.post(
        "/api/auth/login",
        json={"email": "user1@example.com", "password": "SecurePass123!"},
    )
    user1_headers = {"Authorization": f"Bearer {login1.json()['access_token']}"}

    # Login as user2
    login2 = await client.post(
        "/api/auth/login",
        json={"email": "user2@example.com", "password": "SecurePass123!"},
    )
    user2_headers = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    # Both leave their auto-created households
    await client.post("/api/households/leave", headers=user1_headers)
    await client.post("/api/households/leave", headers=user2_headers)

    # Create invite link
    create_response = await client.post(
        f"/api/households/{test_household['id']}/invite-links",
        headers=test_user_headers,
        json={"expires_in_days": 7},
    )
    code = create_response.json()["code"]

    # User1 joins successfully
    join1 = await client.post(
        "/api/households/join",
        headers=user1_headers,
        json={"code": code},
    )
    assert join1.status_code == status.HTTP_200_OK

    # User2 tries to use same code - should fail
    join2 = await client.post(
        "/api/households/join",
        headers=user2_headers,
        json={"code": code},
    )
    assert join2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already been used" in join2.json()["detail"]


@pytest.mark.asyncio
async def test_cannot_join_if_already_in_household(
    client: AsyncClient,
    test_user_headers: dict,
    test_household: dict,
):
    """Test that users already in a household cannot join another."""
    # Create invite link
    create_response = await client.post(
        f"/api/households/{test_household['id']}/invite-links",
        headers=test_user_headers,
        json={"expires_in_days": 7},
    )
    code = create_response.json()["code"]

    # Try to join (but already in a household)
    join_response = await client.post(
        "/api/households/join",
        headers=test_user_headers,
        json={"code": code},
    )

    assert join_response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already in" in join_response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_leave_household(client: AsyncClient, test_user_headers: dict):
    """Test leaving a household."""
    # Leave household (owner with no other members)
    response = await client.post("/api/households/leave", headers=test_user_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["household_deleted"] is True
    assert "deleted" in data["message"].lower()


@pytest.mark.asyncio
async def test_code_case_insensitive(
    client: AsyncClient, test_user_headers: dict, test_household: dict, db: AsyncSession
):
    """Test that codes work case-insensitively."""
    # Create invite link
    invite_link = await household_service.create_invite_link(
        db, test_household["id"], test_household["owner_user_id"], 7
    )
    code = invite_link.code

    # Try to fetch with uppercase
    uppercase_code = code.upper()
    response = await client.get(f"/api/households/join/{uppercase_code}")

    # Should still work (case-insensitive)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == code
