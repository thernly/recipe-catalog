"""
Tests for import and export endpoints
"""

import json
from datetime import UTC, datetime
from io import BytesIO

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import Collection
from app.models.household import Household, HouseholdMember
from app.models.recipe import Recipe
from app.models.user import User
from app.utils.pdf_export import UNICODE_FONT_AVAILABLE


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
async def auth_headers(client: AsyncClient, test_user: User, test_household: Household):
    """Authenticate test user (sets cookies automatically)."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword",
        },
    )

    if response.status_code != 200:
        return {}

    # Extract token from cookies
    token = response.cookies.get("access_token")
    csrf_token = response.cookies.get("csrf_token")

    headers = {"Authorization": f"Bearer {token}"}
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token

    return headers


@pytest.mark.asyncio
async def test_import_single_recipe_from_file(
    client: AsyncClient, auth_headers: dict, test_household: Household
):
    """Test importing a single recipe from JSON file"""
    recipe_data = {
        "name": "Test Recipe",
        "description": "A test recipe",
        "recipeIngredient": ["1 cup flour", "2 eggs"],
        "recipeInstructions": [{"text": "Mix ingredients"}, {"text": "Bake at 350F"}],
        "recipeYield": "4 servings",
        "prepTime": "PT15M",
        "cookTime": "PT30M",
        "totalTime": "PT45M",
        "recipeCategory": "Dessert",
        "recipeCuisine": "American",
    }

    json_content = json.dumps(recipe_data)
    files = {"file": ("recipe.json", BytesIO(json_content.encode()), "application/json")}
    data = {"duplicate_handling": "skip"}

    response = await client.post(
        "/api/v1/import/recipes", data=data, files=files, headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["details"]["created"] == 1
    assert result["details"]["failed"] == 0


@pytest.mark.asyncio
async def test_import_multiple_recipes_from_file(
    client: AsyncClient, auth_headers: dict, test_household: Household
):
    """Test importing multiple recipes from JSON file"""
    recipes_data = [
        {
            "name": "Recipe 1",
            "description": "First recipe",
            "recipeIngredient": ["ingredient 1"],
            "recipeInstructions": [{"text": "step 1"}],
        },
        {
            "name": "Recipe 2",
            "description": "Second recipe",
            "recipeIngredient": ["ingredient 2"],
            "recipeInstructions": [{"text": "step 2"}],
        },
    ]

    json_content = json.dumps(recipes_data)
    files = {"file": ("recipes.json", BytesIO(json_content.encode()), "application/json")}
    data = {"duplicate_handling": "skip"}

    response = await client.post(
        "/api/v1/import/recipes", data=data, files=files, headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result["details"]["created"] == 2


@pytest.mark.asyncio
async def test_import_duplicate_handling_skip(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Test duplicate handling with 'skip' option"""
    # Create existing recipe
    existing_recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="Existing Recipe",
        description="Already exists",
        recipe_data={"recipeIngredient": ["old ingredient"]},
    )
    test_db.add(existing_recipe)
    await test_db.commit()

    # Try to import duplicate
    recipe_data = {
        "name": "Existing Recipe",
        "description": "New description",
        "recipeIngredient": ["new ingredient"],
    }

    json_content = json.dumps(recipe_data)
    files = {"file": ("recipe.json", BytesIO(json_content.encode()), "application/json")}
    data = {"duplicate_handling": "skip"}

    response = await client.post(
        "/api/v1/import/recipes", data=data, files=files, headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result["details"]["skipped"] == 1
    assert result["details"]["created"] == 0


@pytest.mark.asyncio
async def test_import_duplicate_handling_update(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Test duplicate handling with 'update' option"""
    # Create existing recipe
    existing_recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="Recipe to Update",
        description="Old description",
        recipe_data={"recipeIngredient": ["old ingredient"]},
    )
    test_db.add(existing_recipe)
    await test_db.commit()

    # Import with update
    recipe_data = {
        "name": "Recipe to Update",
        "description": "New description",
        "recipeIngredient": ["new ingredient"],
        "recipeInstructions": [{"text": "new step"}],
    }

    json_content = json.dumps(recipe_data)
    files = {"file": ("recipe.json", BytesIO(json_content.encode()), "application/json")}
    data = {"duplicate_handling": "update"}

    response = await client.post(
        "/api/v1/import/recipes", data=data, files=files, headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result["details"]["updated"] == 1
    assert result["details"]["created"] == 0

    # Verify update
    await test_db.refresh(existing_recipe)
    assert existing_recipe.description == "New description"
    assert "new ingredient" in str(existing_recipe.recipe_data)


@pytest.mark.asyncio
async def test_import_duplicate_handling_create(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Test duplicate handling with 'create' option (allows duplicates)"""
    # Create existing recipe
    existing_recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="Duplicate Name",
        description="First one",
        recipe_data={},
    )
    test_db.add(existing_recipe)
    await test_db.commit()

    # Import with create (should create duplicate)
    recipe_data = {
        "name": "Duplicate Name",
        "description": "Second one",
        "recipeIngredient": ["ingredient"],
    }

    json_content = json.dumps(recipe_data)
    files = {"file": ("recipe.json", BytesIO(json_content.encode()), "application/json")}
    data = {"duplicate_handling": "create"}

    response = await client.post(
        "/api/v1/import/recipes", data=data, files=files, headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result["details"]["created"] == 1

    # Verify both exist
    recipes = await test_db.execute(
        select(Recipe).where(Recipe.user_id == test_user.id).where(Recipe.name == "Duplicate Name")
    )
    all_recipes = recipes.scalars().all()
    assert len(all_recipes) == 2


@pytest.mark.asyncio
async def test_import_to_collection(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Test importing recipes directly into a collection"""
    # Create collection
    collection = Collection(user_id=test_user.id, name="Test Collection", description="For imports")
    test_db.add(collection)
    await test_db.commit()

    recipe_data = {
        "name": "Recipe for Collection",
        "description": "Goes into collection",
        "recipeIngredient": ["ingredient"],
    }

    json_content = json.dumps(recipe_data)
    files = {"file": ("recipe.json", BytesIO(json_content.encode()), "application/json")}
    data = {"duplicate_handling": "skip", "collection_id": str(collection.id)}

    response = await client.post(
        "/api/v1/import/recipes", data=data, files=files, headers=auth_headers
    )

    assert response.status_code == 200

    # Verify recipe is in collection
    response = await client.get(
        f"/api/v1/collections/{collection.id}/recipes", headers=auth_headers
    )
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 1
    assert recipes[0]["name"] == "Recipe for Collection"


@pytest.mark.asyncio
async def test_import_invalid_json(
    client: AsyncClient, auth_headers: dict, test_household: Household
):
    """Test importing invalid JSON file"""
    files = {"file": ("invalid.json", BytesIO(b"not valid json"), "application/json")}
    data = {"duplicate_handling": "skip"}

    response = await client.post(
        "/api/v1/import/recipes", data=data, files=files, headers=auth_headers
    )

    assert response.status_code == 400
    assert "Invalid JSON" in response.json()["message"]


@pytest.mark.asyncio
async def test_import_non_json_file(
    client: AsyncClient, auth_headers: dict, test_household: Household
):
    """Test importing non-JSON file"""
    files = {"file": ("recipe.txt", BytesIO(b"some text"), "text/plain")}
    data = {"duplicate_handling": "skip"}

    response = await client.post(
        "/api/v1/import/recipes", data=data, files=files, headers=auth_headers
    )

    assert response.status_code == 400
    assert "must be a JSON file" in response.json()["message"]


@pytest.mark.asyncio
async def test_import_recipes_json_endpoint(
    client: AsyncClient, auth_headers: dict, test_household: Household
):
    """Test importing recipes via JSON API endpoint (not file upload)"""
    recipes = [
        {"name": "API Recipe 1", "description": "From API", "recipeIngredient": ["ingredient 1"]},
        {
            "name": "API Recipe 2",
            "description": "Also from API",
            "recipeIngredient": ["ingredient 2"],
        },
    ]

    response = await client.post(
        "/api/v1/import/recipes/json?duplicate_handling=skip",
        json=recipes,
        headers=auth_headers,
    )

    assert response.status_code == 200
    result = response.json()
    assert result["details"]["created"] == 2


@pytest.mark.asyncio
async def test_export_recipes_json(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Test exporting recipes as JSON"""
    # Create test recipes
    recipe1 = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="Export Recipe 1",
        description="First export",
        recipe_data={
            "recipeIngredient": ["ingredient 1"],
            "recipeInstructions": [{"text": "step 1"}],
        },
    )
    recipe2 = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="Export Recipe 2",
        description="Second export",
        recipe_data={"recipeIngredient": ["ingredient 2"]},
    )
    test_db.add_all([recipe1, recipe2])
    await test_db.commit()

    response = await client.get("/api/v1/export/recipes?format=json", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]

    # Parse exported data
    data = json.loads(response.content)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] in ["Export Recipe 1", "Export Recipe 2"]


@pytest.mark.asyncio
async def test_export_recipes_markdown(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Test exporting recipes as Markdown"""
    recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="Markdown Recipe",
        description="For markdown export",
        recipe_data={
            "recipeIngredient": ["1 cup flour", "2 eggs"],
            "recipeInstructions": [{"text": "Mix ingredients"}, {"text": "Bake"}],
            "recipeYield": "4 servings",
        },
    )
    test_db.add(recipe)
    await test_db.commit()

    response = await client.get("/api/v1/export/recipes?format=markdown", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")

    content = response.content.decode()
    assert "Markdown Recipe" in content
    assert "For markdown export" in content
    assert "1 cup flour" in content
    assert "Mix ingredients" in content


@pytest.mark.asyncio
async def test_export_recipes_text(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Test exporting recipes as plain text"""
    recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="Text Recipe",
        description="For text export",
        recipe_data={
            "recipeIngredient": ["ingredient"],
            "recipeInstructions": [{"text": "do something"}],
        },
    )
    test_db.add(recipe)
    await test_db.commit()

    response = await client.get("/api/v1/export/recipes?format=text", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")

    content = response.content.decode()
    assert "TEXT RECIPE" in content
    assert "ingredient" in content


@pytest.mark.asyncio
async def test_export_collections_json(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Test exporting collections as JSON"""
    # Create collection with recipes
    collection = Collection(
        user_id=test_user.id, name="Export Collection", description="Collection for export"
    )
    test_db.add(collection)
    await test_db.commit()

    # Add recipe to collection - create recipe directly in database
    recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="Collection Recipe",
        description="In collection",
        recipe_data={},
    )
    test_db.add(recipe)
    await test_db.commit()
    await test_db.refresh(recipe)

    await client.post(
        f"/api/v1/collections/{collection.id}/recipes",
        json={"recipe_id": recipe.id},
        headers=auth_headers,
    )

    # Export collections
    response = await client.get("/api/v1/export/collections?format=json", headers=auth_headers)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["total_collections"] >= 1
    assert any(c["name"] == "Export Collection" for c in data["collections"])


@pytest.mark.asyncio
async def test_export_collections_markdown(
    client: AsyncClient, test_user, test_db, auth_headers: dict
):
    """Test exporting collections as Markdown"""
    collection = Collection(
        user_id=test_user.id, name="Markdown Collection", description="For markdown"
    )
    test_db.add(collection)
    await test_db.commit()

    response = await client.get("/api/v1/export/collections?format=markdown", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")

    content = response.content.decode()
    assert "Markdown Collection" in content


@pytest.mark.asyncio
async def test_export_all_data(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Test exporting all user data"""
    # Create some data
    recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="Complete Export Recipe",
        description="For complete export",
        recipe_data={},
    )
    collection = Collection(user_id=test_user.id, name="Complete Export Collection")
    test_db.add_all([recipe, collection])
    await test_db.commit()

    response = await client.get("/api/v1/export/all", headers=auth_headers)

    assert response.status_code == 200
    data = json.loads(response.content)

    assert data["export_type"] == "complete_backup"
    assert "user" in data
    assert "recipes" in data
    assert "collections" in data
    assert "statistics" in data
    assert data["user"]["email"] == test_user.email


@pytest.mark.asyncio
async def test_export_excludes_deleted_recipes(
    client: AsyncClient, test_user, test_db, auth_headers: dict
):
    """Test that export excludes soft-deleted recipes"""

    # Create normal recipe
    recipe1 = Recipe(
        user_id=test_user.id,
        name="Active Recipe",
        description="Should be exported",
        recipe_data={},
    )
    # Create deleted recipe
    recipe2 = Recipe(
        user_id=test_user.id,
        name="Deleted Recipe",
        description="Should not be exported",
        deleted_at=datetime.now(UTC),
        recipe_data={},
    )
    test_db.add_all([recipe1, recipe2])
    await test_db.commit()

    response = await client.get("/api/v1/export/recipes?format=json", headers=auth_headers)

    assert response.status_code == 200
    data = json.loads(response.content)

    assert len(data) == 1
    assert data[0]["name"] == "Active Recipe"


@pytest.mark.asyncio
async def test_export_recipe_pdf_without_image(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Export a single recipe as PDF when it has no image"""
    recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="PDF No Image",
        description="Recipe without image",
        recipe_data={
            "recipeIngredient": ["1 cup water"],
            "recipeInstructions": [{"text": "Boil water"}],
        },
    )
    test_db.add(recipe)
    await test_db.commit()

    response = await client.get(
        f"/api/v1/recipes/{recipe.id}/export?format=pdf", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_export_recipe_pdf_with_image(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Export a single recipe as PDF when it has an embedded image"""
    # Small 1x1 PNG base64
    small_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII="

    recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="PDF With Image",
        description="Recipe with embedded image",
        recipe_data={
            "recipeIngredient": ["1 cup water"],
            "recipeInstructions": [{"text": "Boil water"}],
            "images": [
                {
                    "url": "http://example.com/image.png",
                    "data": small_png_b64,
                    "mimeType": "image/png",
                }
            ],
        },
    )
    test_db.add(recipe)
    await test_db.commit()

    response = await client.get(
        f"/api/v1/recipes/{recipe.id}/export?format=pdf", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_export_recipe_pdf_with_unicode_punctuation(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Export a recipe containing smart quotes/em-dash/ellipsis - should succeed and not raise font error"""
    name = "Chef’s Special — Today’s Soup"
    description = "A rich and tasty soup… served fresh."

    recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name=name,
        description=description,
        recipe_data={
            "recipeIngredient": ["1 cup water"],
            "recipeInstructions": [{"text": "Simmer and serve."}],
        },
    )
    test_db.add(recipe)
    await test_db.commit()

    response = await client.get(
        f"/api/v1/recipes/{recipe.id}/export?format=pdf", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_export_recipe_pdf_non_latin_characters(
    client: AsyncClient, test_user, test_db, auth_headers: dict, test_household: Household
):
    """Export a recipe with non-Latin characters (requires installed Unicode font)"""

    if not UNICODE_FONT_AVAILABLE:
        pytest.skip("Unicode font not available; skipping non-Latin export test")

    name = "こんにちは 世界"  # Japanese: Hello world
    description = "美味しいスープ"  # Japanese: delicious soup

    recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name=name,
        description=description,
        recipe_data={
            "recipeIngredient": ["1 cup water"],
            "recipeInstructions": [{"text": "Serve warm."}],
        },
    )
    test_db.add(recipe)
    await test_db.commit()

    response = await client.get(
        f"/api/v1/recipes/{recipe.id}/export?format=pdf", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_export_recipe_pdf_exporter_error(
    client: AsyncClient,
    test_user,
    test_db,
    auth_headers: dict,
    test_household: Household,
    monkeypatch,
):
    """When the exporter raises an exception, the endpoint returns 500 with generic message"""
    recipe = Recipe(
        user_id=test_user.id,
        household_id=test_household.id,
        name="PDF Error",
        description="This will trigger an exporter error",
        recipe_data={
            "recipeIngredient": ["1 cup water"],
            "recipeInstructions": [{"text": "Boil water"}],
        },
    )
    test_db.add(recipe)
    await test_db.commit()

    # Monkeypatch the exporter to raise
    def _raise_export(self, recipe):
        raise Exception("boom")

    monkeypatch.setattr("app.services.recipe_export.RecipeExporter.export_pdf", _raise_export)

    response = await client.get(
        f"/api/v1/recipes/{recipe.id}/export?format=pdf", headers=auth_headers
    )

    assert response.status_code == 500
    data = response.json()
    assert data["error_code"] == "INTERNAL_ERROR"
    assert "Failed to generate PDF" in data["message"]


@pytest.mark.asyncio
async def test_import_with_invalid_collection_id(
    client: AsyncClient, auth_headers: dict, test_household: Household
):
    """Test import fails with invalid collection ID"""
    recipe_data = {"name": "Test Recipe", "recipeIngredient": ["ingredient"]}

    json_content = json.dumps(recipe_data)
    files = {"file": ("recipe.json", BytesIO(json_content.encode()), "application/json")}
    data = {
        "duplicate_handling": "skip",
        "collection_id": "99999",  # Non-existent collection
    }

    response = await client.post(
        "/api/v1/import/recipes", data=data, files=files, headers=auth_headers
    )

    assert response.status_code == 404
    assert "Collection not found" in response.json()["message"]


@pytest.mark.asyncio
async def test_import_handles_partial_failures(
    client: AsyncClient, auth_headers: dict, test_household: Household
):
    """Test that import handles partial failures gracefully"""
    recipes_data = [
        {
            "name": "Valid Recipe",
            "recipeIngredient": ["ingredient"],
            "recipeInstructions": [{"text": "step"}],
        },
        {
            # Missing name - should fail validation
            "recipeIngredient": ["ingredient"]
        },
        {"name": "Another Valid Recipe", "recipeIngredient": ["ingredient"]},
    ]

    json_content = json.dumps(recipes_data)
    files = {"file": ("recipes.json", BytesIO(json_content.encode()), "application/json")}
    data = {"duplicate_handling": "skip"}

    response = await client.post(
        "/api/v1/import/recipes", data=data, files=files, headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    # Should create the valid ones and report failure for invalid
    assert result["details"]["created"] == 2
    assert result["details"]["failed"] == 1
    assert len(result["details"]["errors"]) == 1
