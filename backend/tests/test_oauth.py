"""Tests for OAuth/OIDC authentication endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.identity_provider import IdentityProvider
from app.models.user import User


@pytest.mark.asyncio
async def test_list_available_providers(client: AsyncClient):
    """Test listing available OAuth providers."""
    response = await client.get("/api/v1/auth/providers")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_authorize_provider_invalid(client: AsyncClient):
    """Test authorization with invalid provider."""
    response = await client.get("/api/v1/auth/invalid_provider/authorize")

    assert response.status_code == 400
    data = response.json()
    assert "Unknown provider" in data["message"]


@pytest.mark.asyncio
async def test_authorize_provider_not_configured(client: AsyncClient):
    """Test authorization with provider that's not configured."""
    # Google, Microsoft, GitHub should return 503 if not configured in test env
    with patch("app.core.oauth.oauth.create_client", return_value=None):
        response = await client.get("/api/v1/auth/google/authorize")
        assert response.status_code == 503
        assert "not configured" in response.json()["message"]


@pytest.mark.asyncio
async def test_oauth_callback_missing_state(client: AsyncClient):
    """Test OAuth callback with missing state parameter."""
    response = await client.get("/api/v1/auth/google/callback?code=test_code")

    assert response.status_code in [400, 503]  # 400 if no state, 503 if not configured


@pytest.mark.asyncio
async def test_oauth_callback_invalid_state(client: AsyncClient):
    """Test OAuth callback with invalid state."""
    response = await client.get("/api/v1/auth/google/callback?code=test_code&state=invalid_state")

    assert response.status_code in [400, 503]


@pytest.mark.asyncio
async def test_list_linked_providers_requires_auth(client: AsyncClient):
    """Test that listing linked providers requires authentication."""
    response = await client.get("/api/v1/auth/me/providers")
    # 401 Unauthorized is returned when no auth cookie provided
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unlink_provider_requires_auth(client: AsyncClient):
    """Test that unlinking provider requires authentication."""
    response = await client.delete("/api/v1/auth/providers/1")
    # 401 Unauthorized is returned when no auth cookie provided
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_linked_providers_authenticated(client: AsyncClient):
    """Test listing linked providers for authenticated user."""
    # Register and login with unique email
    import uuid

    email = f"test-{uuid.uuid4()}@example.com"

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123",
            "display_name": "Test User",
        },
    )

    # Login (sets cookies automatically)
    await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPassword123"},
    )

    # List linked providers (cookies sent automatically)
    response = await client.get("/api/v1/auth/me/providers")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should be empty initially (no OAuth providers linked)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_unlink_provider_not_found(client: AsyncClient):
    """Test unlinking non-existent provider."""
    # Register and login with unique email
    import uuid

    email = f"test-{uuid.uuid4()}@example.com"

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123",
            "display_name": "Test User",
        },
    )

    # Login (sets cookies automatically)
    await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPassword123"},
    )

    # Try to unlink non-existent provider (cookies sent automatically)
    response = await client.delete("/api/v1/auth/providers/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
@patch("app.core.oauth.oauth.create_client")
async def test_oauth_callback_new_user_flow(mock_create_client, client: AsyncClient, test_db):
    """Test OAuth callback creating new user (mocked)."""
    # Mock OAuth client with async methods
    mock_client = AsyncMock()
    mock_client.authorize_access_token = AsyncMock(
        return_value={
            "userinfo": {
                "sub": "google_123456",
                "email": "newuser@example.com",
                "email_verified": True,
                "name": "New User",
            }
        }
    )
    mock_create_client.return_value = mock_client

    # Create OAuth state in database
    from app.models.oauth_state import OAuthState

    oauth_state = OAuthState.create_state(provider="google", link_user_id=None)
    # Use a fixed token for testing
    oauth_state.token = "test_state"
    test_db.add(oauth_state)
    await test_db.commit()

    # Make callback request
    response = await client.get("/api/v1/auth/google/callback?code=test_code&state=test_state")

    # Should successfully create user and set cookies
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"

    # Check that cookies were set
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
@patch("app.core.oauth.oauth.create_client")
async def test_oauth_callback_auto_link_existing_user(
    mock_create_client, client: AsyncClient, test_db
):
    """Test OAuth callback auto-linking to existing user with verified email."""
    # Create existing user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "existing@example.com",
            "password": "TestPassword123",
            "display_name": "Existing User",
        },
    )

    # Mock OAuth client
    mock_client = AsyncMock()
    mock_client.authorize_access_token = AsyncMock(
        return_value={
            "userinfo": {
                "sub": "google_789",
                "email": "existing@example.com",
                "email_verified": True,
                "name": "Existing User",
            }
        }
    )
    mock_create_client.return_value = mock_client

    # Create OAuth state in database
    from app.models.oauth_state import OAuthState

    oauth_state = OAuthState.create_state(provider="google", link_user_id=None)
    oauth_state.token = "test_state"
    test_db.add(oauth_state)
    await test_db.commit()

    response = await client.get("/api/v1/auth/google/callback?code=test_code&state=test_state")

    # Should successfully link and set cookies
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"

    # Check that cookies were set
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
@patch("app.core.oauth.oauth.create_client")
async def test_oauth_callback_unverified_email_rejects_link(
    mock_create_client, client: AsyncClient, test_db
):
    """Test OAuth callback rejects auto-link if email not verified by provider."""
    # Create existing user with unique email
    import uuid

    email = f"existing-{uuid.uuid4()}@example.com"

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123",
        },
    )

    # Mock OAuth client with unverified email
    mock_client = AsyncMock()
    mock_client.authorize_access_token = AsyncMock(
        return_value={
            "userinfo": {
                "sub": "google_999",
                "email": email,
                "email_verified": False,  # Not verified
                "name": "User",
            }
        }
    )
    mock_create_client.return_value = mock_client

    # Create OAuth state in database
    from app.models.oauth_state import OAuthState

    oauth_state = OAuthState.create_state(provider="google", link_user_id=None)
    oauth_state.token = "test_state"
    test_db.add(oauth_state)
    await test_db.commit()

    response = await client.get("/api/v1/auth/google/callback?code=test_code&state=test_state")

    # Should reject auto-linking
    assert response.status_code == 400
    data = response.json()
    assert "Email not verified" in data["message"]


@pytest.mark.asyncio
async def test_prevent_remove_last_auth_method(client: AsyncClient, test_db):
    """Test prevention of removing last authentication method."""
    # Register user with unique email
    import uuid

    email = f"test-{uuid.uuid4()}@example.com"

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123",
            "display_name": "Test User",
        },
    )

    # Login (sets cookies automatically)
    await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPassword123"},
    )

    # Get user from DB and create a provider link
    from sqlalchemy import select

    result = await test_db.execute(select(User).where(User.email == email))
    user = result.scalar_one()

    # Add provider link
    idp = IdentityProvider(
        user_id=user.id,
        provider_name="google",
        provider_subject="test_123",
        email_at_provider=user.email,
    )
    test_db.add(idp)
    await test_db.commit()
    await test_db.refresh(idp)

    # Remove password to simulate passwordless account
    user.hashed_password = None
    await test_db.commit()

    # Try to unlink the only provider (cookies sent automatically)
    response = await client.delete(f"/api/v1/auth/providers/{idp.id}")

    # Should reject removal
    assert response.status_code == 400
    data = response.json()
    assert "Cannot remove last authentication method" in data["message"]


@pytest.mark.asyncio
async def test_oauth_callback_state_mismatch(client: AsyncClient, test_db):
    """Test OAuth callback with state provider mismatch."""
    from app.models.oauth_state import OAuthState

    # Create state for google
    oauth_state = OAuthState.create_state(provider="google", link_user_id=None)
    oauth_state.token = "test_state"
    test_db.add(oauth_state)
    await test_db.commit()

    # Try to use with microsoft (mismatch)
    with patch("app.core.oauth.oauth.create_client") as mock:
        mock.return_value = AsyncMock()
        response = await client.get(
            "/api/v1/auth/microsoft/callback?code=test_code&state=test_state"
        )

        # Should reject due to state mismatch (if provider is configured)
        # or return 503 if not configured
        assert response.status_code in [400, 503]


@pytest.mark.asyncio
@patch("app.core.oauth.oauth.create_client")
async def test_oauth_creates_default_household(mock_create_client, client: AsyncClient, test_db):
    """Test that OAuth registration automatically creates a default household."""
    from sqlalchemy import select

    from app.models.household import Household, HouseholdMember

    # Mock OAuth client
    mock_client = AsyncMock()
    mock_client.authorize_access_token = AsyncMock(
        return_value={
            "userinfo": {
                "sub": "google_newhousehold",
                "email": "oauth_household@example.com",
                "email_verified": True,
                "name": "OAuth User",
            }
        }
    )
    mock_create_client.return_value = mock_client

    # Create OAuth state in database
    from app.models.oauth_state import OAuthState

    oauth_state = OAuthState.create_state(provider="google", link_user_id=None)
    oauth_state.token = "test_state_household"
    test_db.add(oauth_state)
    await test_db.commit()

    # Make callback request (creates new user via OAuth)
    response = await client.get(
        "/api/v1/auth/google/callback?code=test_code&state=test_state_household"
    )

    # Should successfully create user and set cookies
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"

    # Check that cookies were set
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    # Find the created user
    result = await test_db.execute(select(User).where(User.email == "oauth_household@example.com"))
    user = result.scalar_one()

    # Verify household was created for the user
    result = await test_db.execute(
        select(Household).join(HouseholdMember).where(HouseholdMember.user_id == user.id)
    )
    household = result.scalar_one()
    assert household is not None
    assert household.owner_user_id == user.id
    assert household.name == "OAuth User's Household"  # User-friendly default name

    # Verify user is a member with owner role
    result = await test_db.execute(
        select(HouseholdMember).where(
            HouseholdMember.user_id == user.id,
            HouseholdMember.household_id == household.id,
        )
    )
    membership = result.scalar_one()
    assert membership.role == "owner"
