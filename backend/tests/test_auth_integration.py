"""
Integration tests for complete authentication flows.

Tests the full authentication flow from registration through login, token refresh, and logout.
This addresses issue #44 from the codebase assessment.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_auth_flow_register_to_logout(client: AsyncClient):
    """
    Test complete authentication flow: Register → Login → Token Refresh → Logout

    This integration test verifies that the complete authentication process works end-to-end.
    """
    # Step 1: Register a new user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "integration@example.com",
            "password": "SecurePass123!",
            "display_name": "Integration Test User",
        },
    )
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["email"] == "integration@example.com"
    assert user_data["display_name"] == "Integration Test User"
    assert "id" in user_data

    # Verify cookies were set on registration
    assert "access_token" in register_response.cookies
    assert "refresh_token" in register_response.cookies

    # Step 2: Login with the created user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "integration@example.com",
            "password": "SecurePass123!",
        },
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["message"] == "Login successful"

    # Verify new tokens were issued
    assert "access_token" in login_response.cookies
    assert "refresh_token" in login_response.cookies
    initial_access_token = login_response.cookies.get("access_token")
    initial_refresh_token = login_response.cookies.get("refresh_token")

    # Step 3: Refresh the access token
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={initial_refresh_token}"},
    )
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_response.cookies
    assert "refresh_token" in refresh_response.cookies

    # Verify new tokens were issued (refresh tokens should be different due to rotation)
    new_access_token = refresh_response.cookies.get("access_token")
    new_refresh_token = refresh_response.cookies.get("refresh_token")
    # Refresh tokens are always different due to token rotation security
    assert new_refresh_token != initial_refresh_token

    # Step 4: Verify the refreshed token works by accessing a protected endpoint
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Cookie": f"access_token={new_access_token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "integration@example.com"

    # Step 5: Logout
    logout_response = await client.post(
        "/api/v1/auth/logout",
        headers={"Cookie": f"refresh_token={new_refresh_token}"},
    )
    assert logout_response.status_code == 200

    # Verify tokens were cleared (max_age should be 0 or cookies deleted)
    # Note: httpx may not reflect cookie deletion, so we test by trying to use the token

    # Step 6: Verify old refresh token no longer works after logout
    failed_refresh_response = await client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={new_refresh_token}"},
    )
    assert failed_refresh_response.status_code == 401  # Should be unauthorized


@pytest.mark.asyncio
async def test_auth_flow_with_invalid_credentials(client: AsyncClient):
    """
    Test authentication flow with invalid credentials at different stages.
    """
    # Register a user first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "valid@example.com",
            "password": "SecurePass123!",
            "display_name": "Valid User",
        },
    )

    # Try to login with wrong password
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "valid@example.com",
            "password": "WrongPassword123!",
        },
    )
    assert login_response.status_code == 401

    # Try to login with non-existent user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SecurePass123!",
        },
    )
    assert login_response.status_code == 401


@pytest.mark.asyncio
async def test_auth_flow_with_invalid_refresh_token(client: AsyncClient):
    """
    Test that invalid or expired refresh tokens are rejected.
    """
    # Try to refresh with a completely invalid token
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": "refresh_token=invalid-token-12345"},
    )
    assert refresh_response.status_code == 401

    # Try to refresh without a token
    refresh_response = await client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401


@pytest.mark.asyncio
async def test_auth_flow_creates_default_household(client: AsyncClient):
    """
    Test that registering a new user automatically creates a default household.
    """
    # Step 1: Register
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "household@example.com",
            "password": "SecurePass123!",
            "display_name": "Household Test User",
        },
    )
    assert register_response.status_code == 201

    access_token = register_response.cookies.get("access_token")

    # Step 2: Verify household was created
    household_response = await client.get(
        "/api/v1/households/me",
        headers={"Cookie": f"access_token={access_token}"},
    )
    assert household_response.status_code == 200
    household_data = household_response.json()
    assert (
        household_data["name"] == "Household Test User's Household"
    )  # Default name uses display_name
    assert household_data["owner_user_id"] == register_response.json()["id"]


@pytest.mark.asyncio
async def test_protected_endpoint_requires_authentication(client: AsyncClient):
    """
    Test that protected endpoints require valid authentication.
    """
    # Try to access protected endpoint without token
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401

    # Try with invalid token
    response = await client.get(
        "/api/v1/users/me",
        headers={"Cookie": "access_token=invalid-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration_prevented(client: AsyncClient):
    """
    Test that registering with an already-used email is prevented.
    """
    # Register first user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "SecurePass123!",
            "display_name": "First User",
        },
    )

    # Try to register again with same email
    duplicate_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "DifferentPass123!",
            "display_name": "Second User",
        },
    )
    assert duplicate_response.status_code == 400
    assert "already registered" in duplicate_response.json()["message"].lower()
