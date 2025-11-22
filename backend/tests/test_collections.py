"""
Tests for collection management API endpoints
"""

from datetime import UTC

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import Collection
from app.models.household import Household, HouseholdMember
from app.models.recipe import Recipe
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
    await client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword",
        },
    )
    return {}


@pytest.mark.asyncio
async def test_create_collection(client: AsyncClient, auth_headers: dict):
    """Test creating a new collection"""
    collection_data = {
        "name": "My Favorites",
        "description": "My favorite recipes",
        "icon": "star",
    }

    response = await client.post("/api/collections/", json=collection_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Favorites"
    assert data["description"] == "My favorite recipes"
    assert data["icon"] == "star"
    assert data["is_default"] is False
    assert "id" in data


@pytest.mark.asyncio
async def test_create_collection_duplicate_name(client: AsyncClient, auth_headers: dict, test_db):
    """Test creating a collection with duplicate name fails"""
    # Create first collection
    collection_data = {"name": "Duplicates", "description": "First one"}
    await client.post("/api/collections/", json=collection_data)

    # Try to create duplicate
    response = await client.post("/api/collections/", json=collection_data)

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_collection_minimal_data(client: AsyncClient, auth_headers: dict):
    """Test creating collection with minimal required data"""
    collection_data = {"name": "Minimal Collection"}

    response = await client.post("/api/collections/", json=collection_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Collection"


@pytest.mark.asyncio
async def test_list_collections(client: AsyncClient, auth_headers: dict, test_db):
    """Test listing all collections"""
    # Create a few collections
    await client.post("/api/collections/", json={"name": "Collection 1"})
    await client.post("/api/collections/", json={"name": "Collection 2"})

    response = await client.get("/api/collections/")

    assert response.status_code == 200
    collections = response.json()
    assert len(collections) >= 2
    assert any(c["name"] == "Collection 1" for c in collections)
    assert any(c["name"] == "Collection 2" for c in collections)


@pytest.mark.asyncio
async def test_list_collections_includes_recipe_count(
    client: AsyncClient, auth_headers: dict, test_db
):
    """Test that collection list includes recipe counts"""
    # Create collection
    response = await client.post("/api/collections/", json={"name": "Test Collection"})
    collection_id = response.json()["id"]

    # Create and add recipe
    recipe_response = await client.post(
        "/api/recipes/",
        json={
            "name": "Test Recipe",
            "description": "A test recipe",
            "recipe_data": {"recipeIngredient": ["test ingredient"]},
        },
    )
    recipe_id = recipe_response.json()["id"]

    await client.post(f"/api/collections/{collection_id}/recipes", json={"recipe_ids": [recipe_id]})

    # List collections
    response = await client.get("/api/collections/")

    assert response.status_code == 200
    collections = response.json()
    test_collection = next(c for c in collections if c["id"] == collection_id)
    assert test_collection["recipe_count"] == 1


@pytest.mark.asyncio
async def test_get_collection(client: AsyncClient, auth_headers: dict):
    """Test getting a single collection"""
    # Create collection
    create_response = await client.post(
        "/api/collections/", json={"name": "Get Me", "description": "Test getting"}
    )
    collection_id = create_response.json()["id"]

    response = await client.get(f"/api/collections/{collection_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == collection_id
    assert data["name"] == "Get Me"
    assert data["description"] == "Test getting"


@pytest.mark.asyncio
async def test_get_collection_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting non-existent collection returns 404"""
    response = await client.get("/api/collections/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_collection(client: AsyncClient, auth_headers: dict):
    """Test updating a collection"""
    # Create collection
    create_response = await client.post(
        "/api/collections/", json={"name": "Original Name", "description": "Original"}
    )
    collection_id = create_response.json()["id"]

    # Update collection
    update_data = {
        "name": "Updated Name",
        "description": "Updated description",
        "icon": "bookmark",
    }
    response = await client.patch(f"/api/collections/{collection_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"
    assert data["icon"] == "bookmark"


@pytest.mark.asyncio
async def test_update_collection_partial(client: AsyncClient, auth_headers: dict):
    """Test partial update of collection"""
    # Create collection
    create_response = await client.post(
        "/api/collections/",
        json={"name": "Original", "description": "Keep this", "icon": "star"},
    )
    collection_id = create_response.json()["id"]

    # Update only name
    response = await client.patch(f"/api/collections/{collection_id}", json={"name": "New Name"})

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Keep this"
    assert data["icon"] == "star"


@pytest.mark.asyncio
async def test_update_collection_duplicate_name(client: AsyncClient, auth_headers: dict):
    """Test updating collection to duplicate name fails"""
    # Create two collections
    await client.post("/api/collections/", json={"name": "Collection A"})
    response2 = await client.post("/api/collections/", json={"name": "Collection B"})
    collection_b_id = response2.json()["id"]

    # Try to rename B to A
    response = await client.patch(
        f"/api/collections/{collection_b_id}", json={"name": "Collection A"}
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_collection(client: AsyncClient, auth_headers: dict, test_db):
    """Test deleting a collection"""
    # Create collection
    create_response = await client.post("/api/collections/", json={"name": "To Delete"})
    collection_id = create_response.json()["id"]

    # Delete collection
    response = await client.delete(f"/api/collections/{collection_id}")

    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(f"/api/collections/{collection_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_collection_preserves_recipes(
    client: AsyncClient, auth_headers: dict, test_db
):
    """Test that deleting a collection doesn't delete recipes"""
    # Create collection
    coll_response = await client.post("/api/collections/", json={"name": "Delete Me"})
    collection_id = coll_response.json()["id"]

    # Create and add recipe
    recipe_response = await client.post(
        "/api/recipes/", json={"name": "Keep This Recipe", "recipe_data": {}}
    )
    recipe_id = recipe_response.json()["id"]

    await client.post(f"/api/collections/{collection_id}/recipes", json={"recipe_ids": [recipe_id]})

    # Delete collection
    await client.delete(f"/api/collections/{collection_id}")

    # Verify recipe still exists
    recipe_check = await client.get(f"/api/recipes/{recipe_id}")
    assert recipe_check.status_code == 200


@pytest.mark.asyncio
async def test_cannot_delete_default_collection(
    client: AsyncClient, auth_headers: dict, test_db, test_user: User, test_household: Household
):
    """Test that default collections cannot be deleted"""
    # Create default collection
    default_collection = Collection(
        user_id=test_user.id,
        household_id=test_household.id,
        name="All Recipes",
        is_default=True,
    )
    test_db.add(default_collection)
    await test_db.commit()
    await test_db.refresh(default_collection)

    # Try to delete default collection
    response = await client.delete(f"/api/collections/{default_collection.id}")

    assert response.status_code == 400
    assert "Cannot delete default collection" in response.json()["detail"]


@pytest.mark.asyncio
async def test_add_recipes_to_collection(client: AsyncClient, auth_headers: dict):
    """Test adding recipes to a collection"""
    # Create collection
    coll_response = await client.post("/api/collections/", json={"name": "Recipes"})
    collection_id = coll_response.json()["id"]

    # Create recipes
    recipe1 = await client.post("/api/recipes/", json={"name": "Recipe 1", "recipe_data": {}})
    recipe2 = await client.post("/api/recipes/", json={"name": "Recipe 2", "recipe_data": {}})

    recipe1_id = recipe1.json()["id"]
    recipe2_id = recipe2.json()["id"]

    # Add recipes to collection
    response = await client.post(
        f"/api/collections/{collection_id}/recipes",
        json={"recipe_ids": [recipe1_id, recipe2_id]},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["added"]) == 2
    assert recipe1_id in data["added"]
    assert recipe2_id in data["added"]


@pytest.mark.asyncio
async def test_add_duplicate_recipe_to_collection_skips(client: AsyncClient, auth_headers: dict):
    """Test adding duplicate recipe to collection skips it"""
    # Create collection and recipe
    coll_response = await client.post("/api/collections/", json={"name": "Collection"})
    collection_id = coll_response.json()["id"]

    recipe_response = await client.post("/api/recipes/", json={"name": "Recipe", "recipe_data": {}})
    recipe_id = recipe_response.json()["id"]

    # Add recipe first time
    await client.post(f"/api/collections/{collection_id}/recipes", json={"recipe_ids": [recipe_id]})

    # Add same recipe again
    response = await client.post(
        f"/api/collections/{collection_id}/recipes", json={"recipe_ids": [recipe_id]}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["skipped"]) == 1
    assert recipe_id in data["skipped"]


@pytest.mark.asyncio
async def test_add_nonexistent_recipe_to_collection(client: AsyncClient, auth_headers: dict):
    """Test adding non-existent recipe to collection"""
    coll_response = await client.post("/api/collections/", json={"name": "Collection"})
    collection_id = coll_response.json()["id"]

    response = await client.post(
        f"/api/collections/{collection_id}/recipes", json={"recipe_ids": [99999]}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["not_found"]) == 1
    assert 99999 in data["not_found"]


@pytest.mark.asyncio
async def test_remove_recipes_from_collection(client: AsyncClient, auth_headers: dict):
    """Test removing recipes from a collection"""
    # Create collection and recipe
    coll_response = await client.post("/api/collections/", json={"name": "Collection"})
    collection_id = coll_response.json()["id"]

    recipe_response = await client.post("/api/recipes/", json={"name": "Recipe", "recipe_data": {}})
    recipe_id = recipe_response.json()["id"]

    # Add recipe
    await client.post(f"/api/collections/{collection_id}/recipes", json={"recipe_ids": [recipe_id]})

    # Remove recipe
    response = await client.request(
        "DELETE",
        f"/api/collections/{collection_id}/recipes",
        json={"recipe_ids": [recipe_id]},
    )

    assert response.status_code == 204

    # Verify removed
    recipes_response = await client.get(f"/api/collections/{collection_id}/recipes")
    recipes = recipes_response.json()
    assert len(recipes) == 0


@pytest.mark.asyncio
async def test_get_collection_recipes(client: AsyncClient, auth_headers: dict):
    """Test getting all recipes in a collection"""
    # Create collection
    coll_response = await client.post("/api/collections/", json={"name": "Collection"})
    collection_id = coll_response.json()["id"]

    # Create recipes
    recipe1 = await client.post("/api/recipes/", json={"name": "Recipe 1", "recipe_data": {}})
    recipe2 = await client.post("/api/recipes/", json={"name": "Recipe 2", "recipe_data": {}})

    recipe1_id = recipe1.json()["id"]
    recipe2_id = recipe2.json()["id"]

    # Add recipes to collection
    await client.post(
        f"/api/collections/{collection_id}/recipes",
        json={"recipe_ids": [recipe1_id, recipe2_id]},
    )

    # Get recipes
    response = await client.get(f"/api/collections/{collection_id}/recipes")

    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 2
    recipe_names = [r["name"] for r in recipes]
    assert "Recipe 1" in recipe_names
    assert "Recipe 2" in recipe_names


@pytest.mark.asyncio
async def test_get_collection_recipes_excludes_deleted(
    client: AsyncClient, auth_headers: dict, test_db
):
    """Test that getting collection recipes excludes soft-deleted recipes"""
    from datetime import datetime

    # Create collection
    coll_response = await client.post("/api/collections/", json={"name": "Collection"})
    collection_id = coll_response.json()["id"]

    # Create active recipe
    recipe1 = await client.post("/api/recipes/", json={"name": "Active Recipe", "recipe_data": {}})
    recipe1_id = recipe1.json()["id"]

    # Create recipe that will be deleted
    recipe2 = await client.post("/api/recipes/", json={"name": "To Delete", "recipe_data": {}})
    recipe2_id = recipe2.json()["id"]

    # Add both to collection
    await client.post(
        f"/api/collections/{collection_id}/recipes",
        json={"recipe_ids": [recipe1_id, recipe2_id]},
    )

    # Soft delete second recipe
    deleted_recipe = await test_db.execute(select(Recipe).where(Recipe.id == recipe2_id))
    recipe_to_delete = deleted_recipe.scalar_one()
    recipe_to_delete.deleted_at = datetime.now(UTC)
    await test_db.commit()

    # Get collection recipes
    response = await client.get(f"/api/collections/{collection_id}/recipes")

    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 1
    assert recipes[0]["name"] == "Active Recipe"


@pytest.mark.asyncio
async def test_collection_not_found_when_adding_recipes(client: AsyncClient, auth_headers: dict):
    """Test adding recipes to non-existent collection"""
    response = await client.post("/api/collections/99999/recipes", json={"recipe_ids": [1]})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_collection_not_found_when_removing_recipes(client: AsyncClient, auth_headers: dict):
    """Test removing recipes from non-existent collection"""
    response = await client.request(
        "DELETE", "/api/collections/99999/recipes", json={"recipe_ids": [1]}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_recipes_from_nonexistent_collection(client: AsyncClient, auth_headers: dict):
    """Test getting recipes from non-existent collection"""
    response = await client.get("/api/collections/99999/recipes")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_nonexistent_collection(client: AsyncClient, auth_headers: dict):
    """Test updating non-existent collection"""
    response = await client.patch("/api/collections/99999", json={"name": "New Name"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_collection(client: AsyncClient, auth_headers: dict):
    """Test deleting non-existent collection"""
    response = await client.delete("/api/collections/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_empty_collection_has_zero_recipe_count(client: AsyncClient, auth_headers: dict):
    """Test that empty collection has recipe count of 0"""
    response = await client.post("/api/collections/", json={"name": "Empty"})
    collection_id = response.json()["id"]

    get_response = await client.get(f"/api/collections/{collection_id}")

    assert get_response.status_code == 200
    assert get_response.json()["recipe_count"] == 0


@pytest.mark.asyncio
async def test_get_empty_collection_recipes(client: AsyncClient, auth_headers: dict):
    """Test getting recipes from empty collection returns empty list"""
    response = await client.post("/api/collections/", json={"name": "Empty"})
    collection_id = response.json()["id"]

    recipes_response = await client.get(f"/api/collections/{collection_id}/recipes")

    assert recipes_response.status_code == 200
    assert recipes_response.json() == []


@pytest.mark.asyncio
async def test_add_multiple_recipes_mixed_results(client: AsyncClient, auth_headers: dict):
    """Test adding multiple recipes with mixed results (some exist, some don't)"""
    # Create collection
    coll_response = await client.post("/api/collections/", json={"name": "Collection"})
    collection_id = coll_response.json()["id"]

    # Create one recipe
    recipe_response = await client.post("/api/recipes/", json={"name": "Exists", "recipe_data": {}})
    existing_recipe_id = recipe_response.json()["id"]

    # Try to add existing recipe and non-existent recipe
    response = await client.post(
        f"/api/collections/{collection_id}/recipes",
        json={"recipe_ids": [existing_recipe_id, 99999]},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["added"]) == 1
    assert existing_recipe_id in data["added"]
    assert len(data["not_found"]) == 1
    assert 99999 in data["not_found"]


@pytest.mark.asyncio
async def test_collection_includes_creator_display_name(
    client: AsyncClient, auth_headers: dict, test_user: User
):
    """Test that collection includes creator display name"""
    response = await client.post("/api/collections/", json={"name": "Test"})

    assert response.status_code == 201
    data = response.json()
    assert "creator_display_name" in data
    assert data["creator_display_name"] == test_user.display_name
