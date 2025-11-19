"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123",
            "display_name": "Test User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data  # Should not expose password


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email."""
    # Register first user
    await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123",
            "display_name": "Test User",
        },
    )

    # Try to register again with same email
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "DifferentPassword123",
            "display_name": "Another User",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_invalid_password_too_short(client: AsyncClient):
    """Test registration with password that's too short."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "Short1",  # Less than 12 characters
            "display_name": "Test User",
        },
    )

    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_register_invalid_password_no_uppercase(client: AsyncClient):
    """Test registration with password missing uppercase letter."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "alllowercase123",  # No uppercase
            "display_name": "Test User",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_invalid_password_no_lowercase(client: AsyncClient):
    """Test registration with password missing lowercase letter."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "ALLUPPERCASE123",  # No lowercase
            "display_name": "Test User",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_invalid_password_no_digit(client: AsyncClient):
    """Test registration with password missing digit."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "NoDigitsHere",  # No digits
            "display_name": "Test User",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Test registration with invalid email format."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "password": "ValidPassword123",
            "display_name": "Test User",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    # First register a user
    await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123",
            "display_name": "Test User",
        },
    )

    # Then try to login
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"

    # Check that cookies are set
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test login with incorrect password."""
    # First register a user
    await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123",
            "display_name": "Test User",
        },
    )

    # Try to login with wrong password
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent email."""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Test logout endpoint."""
    response = await client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"


@pytest.mark.asyncio
async def test_csrf_token_generation(client: AsyncClient):
    """Test CSRF token generation endpoint."""
    response = await client.get("/api/auth/csrf-token")

    assert response.status_code == 200
    data = response.json()
    assert "csrf_token" in data
    assert isinstance(data["csrf_token"], str)
    assert len(data["csrf_token"]) > 0


@pytest.mark.asyncio
async def test_csrf_token_validation(client: AsyncClient):
    """Test CSRF token validation using the dependency."""
    from app.core.dependencies import validate_csrf
    from fastapi import HTTPException

    # Get a valid token
    response = await client.get("/api/auth/csrf-token")
    token = response.json()["csrf_token"]

    # Valid token should not raise exception
    result = await validate_csrf(x_csrf_token=token)
    assert result == token

    # Invalid token should raise exception
    with pytest.raises(HTTPException) as exc_info:
        await validate_csrf(x_csrf_token="invalid_token")
    assert exc_info.value.status_code == 403
    assert "Invalid CSRF token" in str(exc_info.value.detail)

    # Missing token should raise exception
    with pytest.raises(HTTPException) as exc_info:
        await validate_csrf(x_csrf_token=None)
    assert exc_info.value.status_code == 403
    assert "CSRF token is missing" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_register_creates_default_household(client: AsyncClient, db: AsyncSession):
    """Test that user registration automatically creates a default household."""
    from app.models.household import Household, HouseholdMember
    from app.models.user import User
    from sqlalchemy import select

    # Register a new user
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newhousehold@example.com",
            "password": "TestPassword123",
            "display_name": "John Doe",
        },
    )

    assert response.status_code == 201
    user_data = response.json()
    user_id = user_data["id"]

    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    assert user.email == "newhousehold@example.com"
    assert user.display_name == "John Doe"

    # Verify household was created for the user
    result = await db.execute(
        select(Household)
        .join(HouseholdMember)
        .where(HouseholdMember.user_id == user_id)
    )
    household = result.scalar_one()
    assert household is not None
    assert household.owner_user_id == user_id
    assert household.name == "John Doe's Household"  # User-friendly default name

    # Verify user is a member with owner role
    result = await db.execute(
        select(HouseholdMember).where(
            HouseholdMember.user_id == user_id,
            HouseholdMember.household_id == household.id,
        )
    )
    membership = result.scalar_one()
    assert membership.role == "owner"


@pytest.mark.asyncio
async def test_register_household_name_from_email(client: AsyncClient, db: AsyncSession):
    """Test that household name uses email prefix when display name is not provided."""
    from app.models.household import Household, HouseholdMember
    from sqlalchemy import select

    # Register a user without display name
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "johndoe@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201
    user_data = response.json()
    user_id = user_data["id"]

    # Verify household was created with email-based name
    result = await db.execute(
        select(Household)
        .join(HouseholdMember)
        .where(HouseholdMember.user_id == user_id)
    )
    household = result.scalar_one()
    assert household.name == "johndoe's Household"  # Based on email prefix
