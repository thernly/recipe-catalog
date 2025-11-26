"""Tests for recipe functionality."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.household import Household, HouseholdMember
from app.models.user import User


@pytest_asyncio.fixture
async def test_household(db: AsyncSession, test_user: User):
    """Create a test household."""
    household = Household(
        name="Test Household",
        owner_user_id=test_user.id,
        max_members=10,
    )
    db.add(household)
    await db.commit()
    await db.refresh(household)

    # Add user as household member
    member = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    db.add(member)
    await db.commit()

    return household


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_household: Household):
    """Authenticate test user (sets cookies automatically)."""
    # Login (user already exists from test_user fixture)
    # This sets httpOnly cookies that will be sent automatically with subsequent requests
    await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword",  # The hashed password in conftest.py is for "testpassword"
        },
    )

    # Return empty dict for backwards compatibility with tests that use headers=auth_headers
    return {}


@pytest.mark.asyncio
async def test_create_recipe_success(client: AsyncClient, auth_headers: dict):
    """Test successful recipe creation."""
    recipe_data = {
        "name": "Test Recipe",
        "description": "A delicious test recipe",
        "recipe_data": {
            "ingredients": ["1 cup flour", "2 eggs"],
            "instructions": ["Mix ingredients", "Bake at 350F"],
        },
        "cuisine": "Italian",
        "category": "Dessert",
        "total_time_minutes": 30,
    }

    response = await client.post(
        "/api/v1/recipes/",
        json=recipe_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Recipe"
    assert data["description"] == "A delicious test recipe"
    assert data["cuisine"] == "Italian"
    assert data["category"] == "Dessert"
    assert data["total_time_minutes"] == 30
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_recipe_minimal_data(client: AsyncClient, auth_headers: dict):
    """Test recipe creation with minimal required data."""
    recipe_data = {
        "name": "Simple Recipe",
        "recipe_data": {"ingredients": [], "instructions": []},
    }

    response = await client.post(
        "/api/v1/recipes/",
        json=recipe_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Simple Recipe"
    assert data["description"] is None
    assert data["cuisine"] is None


@pytest.mark.asyncio
async def test_create_recipe_unauthorized(client: AsyncClient):
    """Test recipe creation without authentication."""
    recipe_data = {
        "name": "Test Recipe",
        "recipe_data": {"ingredients": [], "instructions": []},
    }

    response = await client.post("/api/v1/recipes/", json=recipe_data)

    # Expect 403 (Forbidden) due to CSRF protection or 401 (Unauthorized)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_search_recipes_empty(client: AsyncClient, auth_headers: dict):
    """Test searching recipes when none exist."""
    response = await client.get("/api/v1/recipes/search", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["recipes"] == []
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_search_recipes_with_results(client: AsyncClient, auth_headers: dict):
    """Test searching recipes with results."""
    # Create a couple of recipes
    recipe1 = {
        "name": "Pasta Carbonara",
        "description": "Classic Italian pasta",
        "recipe_data": {"ingredients": ["pasta", "eggs", "bacon"], "instructions": []},
        "cuisine": "Italian",
    }
    recipe2 = {
        "name": "Chicken Curry",
        "description": "Spicy Indian curry",
        "recipe_data": {"ingredients": ["chicken", "curry powder"], "instructions": []},
        "cuisine": "Indian",
    }

    await client.post("/api/v1/recipes/", json=recipe1, headers=auth_headers)
    await client.post("/api/v1/recipes/", json=recipe2, headers=auth_headers)

    # Search all recipes
    response = await client.get("/api/v1/recipes/search", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["recipes"]) == 2


@pytest.mark.asyncio
async def test_search_recipes_by_cuisine(client: AsyncClient, auth_headers: dict):
    """Test filtering recipes by cuisine."""
    # Create recipes with different cuisines
    await client.post(
        "/api/v1/recipes/",
        json={
            "name": "Pasta",
            "recipe_data": {"ingredients": [], "instructions": []},
            "cuisine": "Italian",
        },
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/recipes/",
        json={
            "name": "Curry",
            "recipe_data": {"ingredients": [], "instructions": []},
            "cuisine": "Indian",
        },
        headers=auth_headers,
    )

    # Filter by Italian cuisine
    response = await client.get("/api/v1/recipes/search?cuisine=Italian", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["recipes"][0]["cuisine"] == "Italian"


@pytest.mark.asyncio
async def test_search_recipes_with_pagination(client: AsyncClient, auth_headers: dict):
    """Test recipe search with pagination."""
    # Create 5 recipes
    for i in range(5):
        await client.post(
            "/api/v1/recipes/",
            json={
                "name": f"Recipe {i}",
                "recipe_data": {"ingredients": [], "instructions": []},
            },
            headers=auth_headers,
        )

    # Get first page with 2 items
    response = await client.get("/api/v1/recipes/search?page=1&per_page=2", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["recipes"]) == 2
    assert data["page"] == 1
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_get_recipe_by_id(client: AsyncClient, auth_headers: dict):
    """Test getting a specific recipe by ID."""
    # Create a recipe
    create_response = await client.post(
        "/api/v1/recipes/",
        json={
            "name": "Test Recipe",
            "description": "Test description",
            "recipe_data": {"ingredients": [], "instructions": []},
        },
        headers=auth_headers,
    )
    recipe_id = create_response.json()["id"]

    # Get the recipe
    response = await client.get(f"/api/v1/recipes/{recipe_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == recipe_id
    assert data["name"] == "Test Recipe"
    assert data["description"] == "Test description"


@pytest.mark.asyncio
async def test_get_nonexistent_recipe(client: AsyncClient, auth_headers: dict):
    """Test getting a recipe that doesn't exist."""
    response = await client.get("/api/v1/recipes/99999", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_recipe(client: AsyncClient, auth_headers: dict):
    """Test updating a recipe."""
    # Create a recipe
    create_response = await client.post(
        "/api/v1/recipes/",
        json={
            "name": "Original Name",
            "description": "Original description",
            "recipe_data": {"ingredients": [], "instructions": []},
            "cuisine": "Italian",
        },
        headers=auth_headers,
    )
    recipe_id = create_response.json()["id"]

    # Update the recipe
    update_data = {
        "name": "Updated Name",
        "description": "Updated description",
        "cuisine": "French",
    }

    response = await client.patch(
        f"/api/v1/recipes/{recipe_id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"
    assert data["cuisine"] == "French"


@pytest.mark.asyncio
async def test_update_partial_recipe(client: AsyncClient, auth_headers: dict):
    """Test partially updating a recipe."""
    # Create a recipe
    create_response = await client.post(
        "/api/v1/recipes/",
        json={
            "name": "Original Name",
            "description": "Original description",
            "recipe_data": {"ingredients": [], "instructions": []},
        },
        headers=auth_headers,
    )
    recipe_id = create_response.json()["id"]

    # Update only the name
    response = await client.patch(
        f"/api/v1/recipes/{recipe_id}",
        json={"name": "New Name"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Original description"


@pytest.mark.asyncio
async def test_delete_recipe_soft_delete(client: AsyncClient, auth_headers: dict):
    """Test soft deleting a recipe."""
    # Create a recipe
    create_response = await client.post(
        "/api/v1/recipes/",
        json={
            "name": "To Be Deleted",
            "recipe_data": {"ingredients": [], "instructions": []},
        },
        headers=auth_headers,
    )
    recipe_id = create_response.json()["id"]

    # Delete the recipe
    response = await client.delete(f"/api/v1/recipes/{recipe_id}", headers=auth_headers)

    assert response.status_code == 204

    # Verify it's not in search results
    search_response = await client.get("/api/v1/recipes/search", headers=auth_headers)
    assert search_response.json()["total"] == 0

    # Verify it can still be retrieved directly (soft deleted)
    get_response = await client.get(f"/api/v1/recipes/{recipe_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["deleted_at"] is not None


@pytest.mark.asyncio
async def test_restore_deleted_recipe(client: AsyncClient, auth_headers: dict):
    """Test restoring a soft-deleted recipe."""
    # Create and delete a recipe
    create_response = await client.post(
        "/api/v1/recipes/",
        json={
            "name": "Deleted Recipe",
            "recipe_data": {"ingredients": [], "instructions": []},
        },
        headers=auth_headers,
    )
    recipe_id = create_response.json()["id"]

    await client.delete(f"/api/v1/recipes/{recipe_id}", headers=auth_headers)

    # Restore the recipe
    response = await client.post(f"/api/v1/recipes/{recipe_id}/restore", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["deleted_at"] is None

    # Verify it's back in search results
    search_response = await client.get("/api/v1/recipes/search", headers=auth_headers)
    assert search_response.json()["total"] == 1


@pytest.mark.asyncio
async def test_recipe_isolation_between_households(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
):
    """Test that recipes are isolated between different households."""
    # Create a recipe as first user
    await client.post(
        "/api/v1/recipes/",
        json={
            "name": "User 1 Recipe",
            "recipe_data": {"ingredients": [], "instructions": []},
        },
        headers=auth_headers,
    )

    # Create second user with their own household
    user2 = User(
        email="user2@example.com",
        hashed_password="$argon2id$v=19$m=65536,t=3,p=4$YV0apsgMi9zTg238wNnRXw$cUxhIp9ujddyJY06JJ0PtpTnwMunLocdvb+h4LkbrW8",  # "testpassword"
        is_active=True,
        is_verified=True,
        display_name="User 2",
    )
    db.add(user2)
    await db.commit()
    await db.refresh(user2)

    # Create household for user2
    household2 = Household(
        name="Household 2",
        owner_user_id=user2.id,
        max_members=10,
    )
    db.add(household2)
    await db.commit()
    await db.refresh(household2)

    # Add user2 as household member
    member2 = HouseholdMember(
        household_id=household2.id,
        user_id=user2.id,
        role="owner",
    )
    db.add(member2)
    await db.commit()

    # Login as user2 (sets cookies automatically)
    await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user2@example.com",
            "password": "testpassword",
        },
    )

    # User 2 should not see User 1's recipes (cookies sent automatically)
    response = await client.get("/api/v1/recipes/search")

    assert response.status_code == 200
    assert response.json()["total"] == 0
