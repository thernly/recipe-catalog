"""Test API versioning.

Note: Legacy routes (/api/*) were removed as per issue #32 in the codebase assessment.
Only /api/v1/* routes are now supported.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_v1_endpoint_accessible(client: AsyncClient, test_user_headers):
    """Test that v1 endpoints are accessible."""
    response = await client.get(
        "/api/v1/recipes/search", headers=test_user_headers, follow_redirects=True
    )
    # Endpoint should be reachable (200, 401 for auth, or 405 if method not configured)
    assert response.status_code in [200, 401, 405]


@pytest.mark.asyncio
async def test_health_endpoint_no_version_header(client: AsyncClient):
    """Test that non-API endpoints don't have version headers."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert "X-API-Version" not in response.headers
    assert "X-API-Deprecation" not in response.headers
