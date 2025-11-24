"""Test API versioning."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_v1_endpoint_accessible(client: AsyncClient, test_user_headers):
    """Test that v1 endpoints are accessible."""
    response = await client.get("/api/v1/recipes", headers=test_user_headers, follow_redirects=True)
    # Endpoint should be reachable (200, 401 for auth, or 405 if method not configured)
    assert response.status_code in [200, 401, 405]


@pytest.mark.asyncio
async def test_v1_endpoint_has_version_header(client: AsyncClient, test_user_headers):
    """Test that v1 endpoints have version header."""
    response = await client.get("/api/v1/recipes", headers=test_user_headers)
    assert response.headers.get("X-API-Version") == "v1"


@pytest.mark.asyncio
async def test_legacy_endpoint_has_deprecation_warning(client: AsyncClient, test_user_headers):
    """Test that legacy endpoints have deprecation warning."""
    response = await client.get("/api/recipes", headers=test_user_headers)
    assert "X-API-Deprecation" in response.headers
    assert "deprecated" in response.headers["X-API-Deprecation"].lower()
    assert response.headers.get("X-API-Version") == "legacy"


@pytest.mark.asyncio
async def test_legacy_and_v1_endpoints_return_same_data(client: AsyncClient, test_user_headers):
    """Test that legacy and v1 endpoints return equivalent data."""
    legacy_response = await client.get("/api/recipes", headers=test_user_headers)
    v1_response = await client.get("/api/v1/recipes", headers=test_user_headers)

    assert legacy_response.status_code == v1_response.status_code
    # Both should work the same way
    if legacy_response.status_code == 200:
        assert legacy_response.json() == v1_response.json()


@pytest.mark.asyncio
async def test_health_endpoint_no_version_header(client: AsyncClient):
    """Test that non-API endpoints don't have version headers."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert "X-API-Version" not in response.headers
    assert "X-API-Deprecation" not in response.headers
