"""
Tests for recipe format conversion utilities
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from app.utils.recipe_format import (
    convert_to_schema_org,
    convert_from_schema_org,
    _parse_duration_to_minutes,
    _ensure_array,
    _fetch_and_encode_image,
)


class MockRecipe:
    """Mock Recipe model for testing"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.name = kwargs.get("name", "Test Recipe")
        self.description = kwargs.get("description", "Test description")
        self.image_url = kwargs.get("image_url", None)
        self.recipe_data = kwargs.get("recipe_data", {})
        self.source_url = kwargs.get("source_url", None)
        self.source_type = kwargs.get("source_type", "manual")
        self.cuisine = kwargs.get("cuisine", None)
        self.category = kwargs.get("category", None)
        self.total_time_minutes = kwargs.get("total_time_minutes", None)
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))


def test_convert_to_schema_org_basic():
    """Test basic conversion to Schema.org format"""
    recipe = MockRecipe(
        name="Chocolate Cake",
        description="Delicious chocolate cake",
        recipe_data={
            "recipeIngredient": ["2 cups flour", "1 cup sugar"],
            "recipeInstructions": [{"text": "Mix ingredients"}, {"text": "Bake"}],
            "recipeYield": "8 servings",
        },
    )

    result = convert_to_schema_org(recipe)

    assert result["name"] == "Chocolate Cake"
    assert result["description"] == "Delicious chocolate cake"
    assert result["recipeIngredient"] == ["2 cups flour", "1 cup sugar"]
    assert len(result["recipeInstructions"]) == 2
    assert result["recipeYield"] == "8 servings"


def test_convert_to_schema_org_with_times():
    """Test conversion with cooking times"""
    recipe = MockRecipe(
        name="Quick Pasta",
        recipe_data={
            "prepTime": "PT10M",
            "cookTime": "PT20M",
            "totalTime": "PT30M",
        },
    )

    result = convert_to_schema_org(recipe)

    assert result["prepTime"] == "PT10M"
    assert result["cookTime"] == "PT20M"
    assert result["totalTime"] == "PT30M"


def test_convert_to_schema_org_with_category_cuisine():
    """Test conversion with category and cuisine"""
    recipe = MockRecipe(
        name="Pizza",
        category="Dinner",
        cuisine="Italian",
        recipe_data={},
    )

    result = convert_to_schema_org(recipe)

    assert "Dinner" in result["recipeCategory"]
    assert "Italian" in result["recipeCuisine"]


def test_convert_to_schema_org_with_nutrition():
    """Test conversion with nutrition info"""
    recipe = MockRecipe(
        name="Healthy Salad",
        recipe_data={
            "nutrition": {
                "calories": "250",
                "proteinContent": "10g",
                "fatContent": "15g",
            }
        },
    )

    result = convert_to_schema_org(recipe)

    assert result["nutrition"]["calories"] == "250"
    assert result["nutrition"]["proteinContent"] == "10g"


def test_convert_to_schema_org_with_rating():
    """Test conversion with aggregate rating"""
    recipe = MockRecipe(
        name="Popular Recipe",
        recipe_data={
            "aggregateRating": {"ratingValue": "4.5", "ratingCount": "100"}
        },
    )

    result = convert_to_schema_org(recipe)

    assert result["aggregateRating"]["ratingValue"] == "4.5"
    assert result["aggregateRating"]["ratingCount"] == "100"


def test_convert_from_schema_org_basic():
    """Test basic conversion from Schema.org format"""
    schema_recipe = {
        "name": "Test Recipe",
        "description": "A test recipe",
        "recipeIngredient": ["1 cup flour", "2 eggs"],
        "recipeInstructions": [{"text": "Mix"}, {"text": "Bake"}],
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["name"] == "Test Recipe"
    assert result["description"] == "A test recipe"
    assert result["recipe_data"]["recipeIngredient"] == ["1 cup flour", "2 eggs"]


def test_convert_from_schema_org_with_times():
    """Test conversion from Schema.org with time parsing"""
    schema_recipe = {
        "name": "Timed Recipe",
        "prepTime": "PT15M",
        "cookTime": "PT30M",
        "totalTime": "PT45M",
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["total_time_minutes"] == 45
    assert result["recipe_data"]["prepTime"] == "PT15M"
    assert result["recipe_data"]["cookTime"] == "PT30M"


def test_convert_from_schema_org_time_calculation():
    """Test total time calculation from prep and cook times"""
    schema_recipe = {
        "name": "Recipe",
        "prepTime": "PT20M",
        "cookTime": "PT40M",
        # No totalTime specified
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["total_time_minutes"] == 60  # 20 + 40


def test_convert_from_schema_org_category_array():
    """Test conversion with category as array"""
    schema_recipe = {
        "name": "Recipe",
        "recipeCategory": ["Dinner", "Main Course"],
    }

    result = convert_from_schema_org(schema_recipe)

    # Should take first category
    assert result["category"] == "Dinner"
    # Should preserve full array in recipe_data
    assert result["recipe_data"]["recipeCategory"] == ["Dinner", "Main Course"]


def test_convert_from_schema_org_cuisine_string():
    """Test conversion with cuisine as string"""
    schema_recipe = {
        "name": "Recipe",
        "recipeCuisine": "Mexican",
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["cuisine"] == "Mexican"


def test_convert_from_schema_org_sets_source_type():
    """Test that conversion sets source_type to 'imported'"""
    schema_recipe = {
        "name": "Imported Recipe",
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["source_type"] == "imported"


def test_convert_from_schema_org_with_url():
    """Test conversion with source URL"""
    schema_recipe = {
        "name": "Recipe",
        "url": "https://example.com/recipe",
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["source_url"] == "https://example.com/recipe"


def test_parse_duration_iso_minutes():
    """Test parsing ISO 8601 duration with minutes only"""
    assert _parse_duration_to_minutes("PT30M") == 30
    assert _parse_duration_to_minutes("PT5M") == 5


def test_parse_duration_iso_hours():
    """Test parsing ISO 8601 duration with hours"""
    assert _parse_duration_to_minutes("PT1H") == 60
    assert _parse_duration_to_minutes("PT2H") == 120


def test_parse_duration_iso_hours_and_minutes():
    """Test parsing ISO 8601 duration with hours and minutes"""
    assert _parse_duration_to_minutes("PT1H30M") == 90
    assert _parse_duration_to_minutes("PT2H15M") == 135


def test_parse_duration_simple_minutes():
    """Test parsing simple minute format"""
    assert _parse_duration_to_minutes("30 minutes") == 30
    assert _parse_duration_to_minutes("45 mins") == 45
    assert _parse_duration_to_minutes("5 min") == 5


def test_parse_duration_simple_hours():
    """Test parsing simple hour format"""
    assert _parse_duration_to_minutes("1 hour") == 60
    assert _parse_duration_to_minutes("2 hours") == 120
    assert _parse_duration_to_minutes("3 hrs") == 180


def test_parse_duration_simple_combined():
    """Test parsing combined hour and minute format"""
    assert _parse_duration_to_minutes("1 hour 30 minutes") == 90
    assert _parse_duration_to_minutes("2 hrs 15 mins") == 135


def test_parse_duration_empty():
    """Test parsing empty duration"""
    assert _parse_duration_to_minutes("") is None
    assert _parse_duration_to_minutes(None) is None


def test_parse_duration_invalid():
    """Test parsing invalid duration returns None"""
    assert _parse_duration_to_minutes("invalid") is None
    assert _parse_duration_to_minutes("some text") is None


def test_ensure_array_none():
    """Test _ensure_array with None"""
    assert _ensure_array(None) == []


def test_ensure_array_empty_string():
    """Test _ensure_array with empty string"""
    assert _ensure_array("") == []


def test_ensure_array_string():
    """Test _ensure_array with string"""
    assert _ensure_array("test") == ["test"]


def test_ensure_array_list():
    """Test _ensure_array with list"""
    assert _ensure_array(["a", "b"]) == ["a", "b"]


def test_ensure_array_preserves_list():
    """Test _ensure_array preserves existing list"""
    original = ["item1", "item2"]
    result = _ensure_array(original)
    assert result == original


@patch("app.utils.recipe_format.httpx.Client")
def test_fetch_and_encode_image_success(mock_client_class):
    """Test successful image fetch and encoding"""
    # Mock the response
    mock_response = Mock()
    mock_response.content = b"fake image data"
    mock_response.headers = {"Content-Type": "image/png"}
    mock_response.raise_for_status = Mock()

    # Mock the client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = _fetch_and_encode_image("https://example.com/image.png")

    assert result is not None
    assert result["url"] == "https://example.com/image.png"
    assert result["mimeType"] == "image/png"
    assert "data" in result
    assert len(result["data"]) > 0  # Base64 encoded data


@patch("app.utils.recipe_format.httpx.Client")
def test_fetch_and_encode_image_failure(mock_client_class):
    """Test image fetch failure handling"""
    # Mock the client to raise an error
    mock_client = Mock()
    mock_client.get.side_effect = Exception("Network error")
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = _fetch_and_encode_image("https://example.com/image.png")

    assert result is None


def test_fetch_and_encode_image_empty_url():
    """Test fetch with empty URL"""
    assert _fetch_and_encode_image("") is None
    assert _fetch_and_encode_image(None) is None


def test_convert_from_schema_org_with_equipment():
    """Test conversion with equipment field"""
    schema_recipe = {
        "name": "Recipe",
        "equipment": ["Stand mixer", "Baking pan"],
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["recipe_data"]["equipment"] == ["Stand mixer", "Baking pan"]


def test_convert_from_schema_org_with_notes():
    """Test conversion with notes field"""
    schema_recipe = {
        "name": "Recipe",
        "notes": "Can be made ahead and frozen",
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["recipe_data"]["notes"] == "Can be made ahead and frozen"


def test_convert_from_schema_org_with_keywords():
    """Test conversion with keywords"""
    schema_recipe = {
        "name": "Recipe",
        "keywords": "quick, easy, vegetarian",
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["recipe_data"]["keywords"] == "quick, easy, vegetarian"


def test_convert_from_schema_org_missing_name():
    """Test conversion with missing name defaults to 'Untitled Recipe'"""
    schema_recipe = {
        "description": "A recipe without a name",
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["name"] == "Untitled Recipe"


def test_convert_to_schema_org_preserves_all_fields():
    """Test that conversion to Schema.org preserves all stored fields"""
    recipe = MockRecipe(
        name="Complete Recipe",
        description="Full details",
        recipe_data={
            "recipeIngredient": ["ingredient"],
            "recipeInstructions": [{"text": "step"}],
            "equipment": ["tool"],
            "notes": "some notes",
            "keywords": "tags",
            "author": ["Chef Name"],
            "recipeYield": "4",
            "nutrition": {"calories": "200"},
        },
    )

    result = convert_to_schema_org(recipe)

    assert result["recipeIngredient"] == ["ingredient"]
    assert result["recipeInstructions"] == [{"text": "step"}]
    assert result["equipment"] == ["tool"]
    assert result["notes"] == "some notes"
    assert result["keywords"] == "tags"
    assert result["author"] == ["Chef Name"]
    assert result["recipeYield"] == "4"


def test_convert_from_schema_org_handles_string_images():
    """Test conversion handles image as string URL"""
    schema_recipe = {
        "name": "Recipe",
        "image": "https://example.com/image.jpg",
    }

    with patch("app.utils.recipe_format._fetch_and_encode_image") as mock_fetch:
        mock_fetch.return_value = {
            "url": "https://example.com/image.jpg",
            "data": "base64data",
            "mimeType": "image/jpeg",
        }

        result = convert_from_schema_org(schema_recipe)

        assert result["image_url"] == "https://example.com/image.jpg"
        assert len(result["recipe_data"]["images"]) == 1


def test_convert_from_schema_org_handles_dict_images():
    """Test conversion handles image as dict with URL and data"""
    schema_recipe = {
        "name": "Recipe",
        "image": [
            {
                "url": "https://example.com/image.jpg",
                "data": "base64encodeddata",
                "mimeType": "image/jpeg",
            }
        ],
    }

    result = convert_from_schema_org(schema_recipe)

    assert result["image_url"] == "https://example.com/image.jpg"
    assert len(result["recipe_data"]["images"]) == 1
    assert result["recipe_data"]["images"][0]["data"] == "base64encodeddata"


def test_round_trip_conversion():
    """Test converting to Schema.org and back preserves data"""
    original_recipe = MockRecipe(
        name="Round Trip Recipe",
        description="Testing round trip",
        recipe_data={
            "recipeIngredient": ["1 cup flour"],
            "recipeInstructions": [{"text": "Mix"}],
            "prepTime": "PT10M",
            "cookTime": "PT20M",
            "totalTime": "PT30M",
        },
    )

    # Convert to Schema.org
    schema_format = convert_to_schema_org(original_recipe)

    # Convert back
    internal_format = convert_from_schema_org(schema_format)

    # Verify key fields preserved
    assert internal_format["name"] == "Round Trip Recipe"
    assert internal_format["description"] == "Testing round trip"
    assert internal_format["recipe_data"]["recipeIngredient"] == ["1 cup flour"]
    assert internal_format["total_time_minutes"] == 30
