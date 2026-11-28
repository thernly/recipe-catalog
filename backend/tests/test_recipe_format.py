"""
Tests for recipe format conversion utilities
"""

import base64
import io
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image

from app.utils.recipe_format import (
    _ensure_array,
    _fetch_and_encode_image,
    _parse_duration_to_minutes,
    convert_from_schema_org,
    convert_to_schema_org,
    dedupe_recipe_images,
    picture_key,
)
from app.utils.safe_fetch import FetchResult, SafeFetchError


class MockRecipe:
    """Mock Recipe model for testing"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.name = kwargs.get("name", "Test Recipe")
        self.description = kwargs.get("description", "Test description")
        self.image_url = kwargs.get("image_url")
        self.recipe_data = kwargs.get("recipe_data", {})
        self.source_url = kwargs.get("source_url")
        self.source_type = kwargs.get("source_type", "manual")
        self.cuisine = kwargs.get("cuisine")
        self.category_names = kwargs.get("category_names", [])
        self.total_time_minutes = kwargs.get("total_time_minutes")
        self.created_at = kwargs.get("created_at", datetime.now(UTC))


async def test_convert_to_schema_org_basic():
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

    result = await convert_to_schema_org(recipe)

    assert result["name"] == "Chocolate Cake"
    assert result["description"] == "Delicious chocolate cake"
    assert result["recipeIngredient"] == ["2 cups flour", "1 cup sugar"]
    assert len(result["recipeInstructions"]) == 2
    assert result["recipeYield"] == "8 servings"


async def test_convert_to_schema_org_with_times():
    """Test conversion with cooking times"""
    recipe = MockRecipe(
        name="Quick Pasta",
        recipe_data={
            "prepTime": "PT10M",
            "cookTime": "PT20M",
            "totalTime": "PT30M",
        },
    )

    result = await convert_to_schema_org(recipe)

    assert result["prepTime"] == "PT10M"
    assert result["cookTime"] == "PT20M"
    assert result["totalTime"] == "PT30M"


async def test_convert_to_schema_org_with_category_cuisine():
    """Test conversion with category and cuisine"""
    recipe = MockRecipe(
        name="Pizza",
        category_names=["Dinner", "Main Course"],
        cuisine="Italian",
        recipe_data={},
    )

    result = await convert_to_schema_org(recipe)

    assert result["recipeCategory"] == ["Dinner", "Main Course"]
    assert "Italian" in result["recipeCuisine"]


async def test_convert_to_schema_org_with_nutrition():
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

    result = await convert_to_schema_org(recipe)

    assert result["nutrition"]["calories"] == "250"
    assert result["nutrition"]["proteinContent"] == "10g"


async def test_convert_to_schema_org_with_rating():
    """Test conversion with aggregate rating"""
    recipe = MockRecipe(
        name="Popular Recipe",
        recipe_data={"aggregateRating": {"ratingValue": "4.5", "ratingCount": "100"}},
    )

    result = await convert_to_schema_org(recipe)

    assert result["aggregateRating"]["ratingValue"] == "4.5"
    assert result["aggregateRating"]["ratingCount"] == "100"


async def test_convert_from_schema_org_basic():
    """Test basic conversion from Schema.org format"""
    schema_recipe = {
        "name": "Test Recipe",
        "description": "A test recipe",
        "recipeIngredient": ["1 cup flour", "2 eggs"],
        "recipeInstructions": [{"text": "Mix"}, {"text": "Bake"}],
    }

    result = await convert_from_schema_org(schema_recipe)

    assert result["name"] == "Test Recipe"
    assert result["description"] == "A test recipe"
    assert result["recipe_data"]["recipeIngredient"] == ["1 cup flour", "2 eggs"]


async def test_convert_from_schema_org_with_times():
    """Test conversion from Schema.org with time parsing"""
    schema_recipe = {
        "name": "Timed Recipe",
        "prepTime": "PT15M",
        "cookTime": "PT30M",
        "totalTime": "PT45M",
    }

    result = await convert_from_schema_org(schema_recipe)

    assert result["total_time_minutes"] == 45
    assert result["recipe_data"]["prepTime"] == "PT15M"
    assert result["recipe_data"]["cookTime"] == "PT30M"


async def test_convert_from_schema_org_time_calculation():
    """Test total time calculation from prep and cook times"""
    schema_recipe = {
        "name": "Recipe",
        "prepTime": "PT20M",
        "cookTime": "PT40M",
        # No totalTime specified
    }

    result = await convert_from_schema_org(schema_recipe)

    assert result["total_time_minutes"] == 60  # 20 + 40


async def test_convert_from_schema_org_category_array():
    """Test conversion with category as array"""
    schema_recipe = {
        "name": "Recipe",
        "recipeCategory": ["Dinner", "Main Course"],
    }

    result = await convert_from_schema_org(schema_recipe)

    # Every category is kept
    assert result["categories"] == ["Dinner", "Main Course"]
    # Should preserve full array in recipe_data
    assert result["recipe_data"]["recipeCategory"] == ["Dinner", "Main Course"]


async def test_convert_from_schema_org_cuisine_string():
    """Test conversion with cuisine as string"""
    schema_recipe = {
        "name": "Recipe",
        "recipeCuisine": "Mexican",
    }

    result = await convert_from_schema_org(schema_recipe)

    assert result["cuisine"] == "Mexican"


async def test_convert_from_schema_org_sets_source_type():
    """Test that conversion sets source_type to 'imported'"""
    schema_recipe = {
        "name": "Imported Recipe",
    }

    result = await convert_from_schema_org(schema_recipe)

    assert result["source_type"] == "imported"


async def test_convert_from_schema_org_with_url():
    """Test conversion with source URL"""
    schema_recipe = {
        "name": "Recipe",
        "url": "https://example.com/recipe",
    }

    result = await convert_from_schema_org(schema_recipe)

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


@patch("app.utils.recipe_format.safe_fetch", new_callable=AsyncMock)
async def test_fetch_and_encode_image_success(mock_safe_fetch):
    """Test successful image fetch and encoding"""
    mock_safe_fetch.return_value = FetchResult(
        url="https://example.com/image.png", content=b"fake image data", content_type="image/png"
    )

    result = await _fetch_and_encode_image("https://example.com/image.png")

    assert result is not None
    assert result["url"] == "https://example.com/image.png"
    assert result["mimeType"] == "image/png"
    assert base64.b64decode(result["data"]) == b"fake image data"
    # The fetch is size-capped and restricted to the configured image types
    kwargs = mock_safe_fetch.call_args.kwargs
    assert kwargs["max_bytes"] > 0
    assert "image/png" in kwargs["allowed_content_types"]


@patch("app.utils.recipe_format.safe_fetch", new_callable=AsyncMock)
async def test_fetch_and_encode_image_refused(mock_safe_fetch):
    """A URL refused by the safe-fetch helper is stored without data"""
    mock_safe_fetch.side_effect = SafeFetchError("Refusing to fetch from non-public address")

    assert await _fetch_and_encode_image("http://169.254.169.254/latest") is None


@patch("app.utils.recipe_format.safe_fetch", new_callable=AsyncMock)
async def test_fetch_and_encode_image_failure(mock_safe_fetch):
    """Test image fetch failure handling"""
    mock_safe_fetch.side_effect = Exception("Network error")

    result = await _fetch_and_encode_image("https://example.com/image.png")

    assert result is None


async def test_fetch_and_encode_image_empty_url():
    """Test fetch with empty URL"""
    assert await _fetch_and_encode_image("") is None
    assert await _fetch_and_encode_image(None) is None


async def test_convert_from_schema_org_private_image_url_not_fetched():
    """An image URL pointing at a private address is kept but never fetched"""
    with patch("app.utils.safe_fetch.httpx2.AsyncClient") as client_class:
        result = await convert_from_schema_org(
            {"name": "Recipe", "image": "http://127.0.0.1:8000/admin.png"}
        )

    client_class.return_value.__aenter__.return_value.send.assert_not_called()
    assert result["image_url"] == "http://127.0.0.1:8000/admin.png"
    assert result["recipe_data"]["images"] == [
        {"url": "http://127.0.0.1:8000/admin.png", "data": "", "mimeType": "image/jpeg"}
    ]


async def test_convert_from_schema_org_with_equipment():
    """Test conversion with equipment field"""
    schema_recipe = {
        "name": "Recipe",
        "equipment": ["Stand mixer", "Baking pan"],
    }

    result = await convert_from_schema_org(schema_recipe)

    assert result["recipe_data"]["equipment"] == ["Stand mixer", "Baking pan"]


async def test_convert_from_schema_org_with_notes():
    """Test conversion with notes field"""
    schema_recipe = {
        "name": "Recipe",
        "notes": "Can be made ahead and frozen",
    }

    result = await convert_from_schema_org(schema_recipe)

    assert result["recipe_data"]["notes"] == "Can be made ahead and frozen"


async def test_convert_from_schema_org_with_keywords():
    """Test conversion with keywords"""
    schema_recipe = {
        "name": "Recipe",
        "keywords": "quick, easy, vegetarian",
    }

    result = await convert_from_schema_org(schema_recipe)

    assert result["recipe_data"]["keywords"] == "quick, easy, vegetarian"


async def test_convert_from_schema_org_missing_name():
    """Test conversion with missing name raises ValueError"""
    schema_recipe = {
        "description": "A recipe without a name",
    }

    with pytest.raises(ValueError, match="Recipe name is required"):
        await convert_from_schema_org(schema_recipe)


async def test_convert_to_schema_org_preserves_all_fields():
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

    result = await convert_to_schema_org(recipe)

    assert result["recipeIngredient"] == ["ingredient"]
    assert result["recipeInstructions"] == [{"text": "step"}]
    assert result["equipment"] == ["tool"]
    assert result["notes"] == "some notes"
    assert result["keywords"] == "tags"
    assert result["author"] == ["Chef Name"]
    assert result["recipeYield"] == "4"


async def test_convert_from_schema_org_handles_string_images():
    """Test conversion handles image as string URL"""
    schema_recipe = {
        "name": "Recipe",
        "image": "https://example.com/image.jpg",
    }

    with patch(
        "app.utils.recipe_format._fetch_and_encode_image", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = {
            "url": "https://example.com/image.jpg",
            "data": "base64data",
            "mimeType": "image/jpeg",
        }

        result = await convert_from_schema_org(schema_recipe)

        assert result["image_url"] == "https://example.com/image.jpg"
        assert len(result["recipe_data"]["images"]) == 1


async def test_convert_from_schema_org_handles_dict_images():
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

    result = await convert_from_schema_org(schema_recipe)

    assert result["image_url"] == "https://example.com/image.jpg"
    assert len(result["recipe_data"]["images"]) == 1
    assert result["recipe_data"]["images"][0]["data"] == "base64encodeddata"


async def test_round_trip_conversion():
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
    schema_format = await convert_to_schema_org(original_recipe)

    # Convert back
    internal_format = await convert_from_schema_org(schema_format)

    # Verify key fields preserved
    assert internal_format["name"] == "Round Trip Recipe"
    assert internal_format["description"] == "Testing round trip"
    assert internal_format["recipe_data"]["recipeIngredient"] == ["1 cup flour"]
    assert internal_format["total_time_minutes"] == 30


# Addresses from real imports: one picture listed at several sizes or crops
WP = "https://alexandracooks.com/wp-content/uploads/2012/10/pancake211"
NYT = "https://static01.nyt.com/images/2016/06/15/dining/15CRACKERS1/15CRACKERS1"


@pytest.mark.parametrize(
    "first, second",
    [
        (f"{WP}-225x225.jpg", f"{WP}.jpg"),
        (f"{WP}-320x180.jpg", f"{WP}-260x195.jpg"),
        (
            "https://lechefswife.com/wp-content/uploads/2020/12/IMG_2456-scaled-225x225.jpg",
            "https://lechefswife.com/wp-content/uploads/2020/12/IMG_2456-scaled.jpg",
        ),
        (
            "https://junedarville.com/wp-content/uploads/2016/09/Waterzooi-scaled.jpg",
            "https://junedarville.com/wp-content/uploads/2016/09/Waterzooi-500x375.jpg",
        ),
        (f"{NYT}-videoSixteenByNineJumbo1600-v2.jpg", f"{NYT}-facebookJumbo-v2.jpg"),
        (f"{NYT}-mediumSquareAt3X.jpg", f"{NYT}-googleFourByThree.jpg"),
    ],
)
def test_picture_key_matches_sizes_of_one_picture(first, second):
    assert picture_key(first) == picture_key(second)


@pytest.mark.parametrize(
    "first, second",
    [
        # Different photos on one site
        (
            "https://cdn.shopify.com/s/files/1/1250/2125/files/Grissini.jpg?v=1749388970",
            "https://cdn.shopify.com/s/files/1/1250/2125/files/Grissini_cuts.jpg?v=1749388901",
        ),
        # The same name in another upload folder
        (
            "https://example.com/wp-content/uploads/2022/01/soup.jpg",
            "https://example.com/wp-content/uploads/2023/05/soup.jpg",
        ),
        # Left alone: may be different shots
        (
            "https://images.101cookbooks.com/blended-vegetable-soup-h.jpg?w=1200",
            "https://images.101cookbooks.com/blended-vegetable-soup-1.jpg?w=1200",
        ),
    ],
)
def test_picture_key_keeps_different_pictures_apart(first, second):
    assert picture_key(first) != picture_key(second)


def _image(url, size):
    return {"url": url, "data": "x" * size, "mimeType": "image/jpeg"}


async def test_import_keeps_each_picture_once_at_its_largest_size():
    sizes = {
        f"{WP}-225x225.jpg": 10,
        f"{WP}-260x195.jpg": 12,
        f"{WP}.jpg": 90,
        "https://example.com/other.jpg": 40,
    }

    async def fetch(url):
        return _image(url, sizes[url])

    with patch("app.utils.recipe_format._fetch_and_encode_image", side_effect=fetch):
        result = await convert_from_schema_org({"name": "Dutch Baby", "image": list(sizes)})

    kept = result["recipe_data"]["images"]
    assert [image["url"] for image in kept] == [f"{WP}.jpg", "https://example.com/other.jpg"]
    assert result["image_url"] == f"{WP}.jpg"


async def test_import_counts_the_five_picture_limit_after_matching_sizes():
    urls = [f"https://example.com/p{n}-500x500.jpg" for n in range(6)]
    urls.insert(1, "https://example.com/p0-480x270.jpg")

    async def fetch(url):
        return _image(url, 5)

    with patch("app.utils.recipe_format._fetch_and_encode_image", side_effect=fetch):
        result = await convert_from_schema_org({"name": "Many", "image": urls})

    assert len(result["recipe_data"]["images"]) == 5
    assert result["recipe_data"]["images"][1]["url"] == "https://example.com/p1-500x500.jpg"


def test_dedupe_recipe_images_keeps_the_largest_copy_where_the_picture_first_appeared():
    thumb, full = _image(f"{WP}-225x225.jpg", 10), _image(f"{WP}.jpg", 90)
    other = _image("https://example.com/other.jpg", 40)
    no_address = {"url": "", "data": "abc", "mimeType": "image/png"}
    recipe = MockRecipe(
        image_url=thumb["url"],
        recipe_data={"name": "Dutch Baby", "images": [thumb, other, full, no_address]},
    )

    dropped = dedupe_recipe_images(recipe)

    assert dropped == [thumb]
    assert recipe.recipe_data["images"] == [full, other, no_address]
    assert recipe.recipe_data["name"] == "Dutch Baby"
    assert recipe.image_url == full["url"]


def _png(width, height, noisy):
    picture = Image.new("RGB", (width, height), "white")
    if noisy:  # noise compresses badly, so a small picture makes a big file
        picture = Image.frombytes("RGB", (width, height), os.urandom(width * height * 3))
    buffer = io.BytesIO()
    picture.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def test_dedupe_recipe_images_keeps_the_most_pixels_not_the_biggest_file():
    small_big_file = {"url": f"{WP}-500x500.jpg", "data": _png(60, 60, True), "mimeType": "x"}
    large_small_file = {"url": f"{WP}-scaled.jpg", "data": _png(400, 300, False), "mimeType": "x"}
    assert len(small_big_file["data"]) > len(large_small_file["data"])
    recipe = MockRecipe(recipe_data={"images": [small_big_file, large_small_file]})

    dedupe_recipe_images(recipe)

    assert recipe.recipe_data["images"] == [large_small_file]


def test_dedupe_recipe_images_leaves_distinct_pictures_alone():
    images = [_image("https://example.com/a.jpg", 5), _image("https://example.com/b.jpg", 5)]
    recipe = MockRecipe(image_url="https://example.com/a.jpg", recipe_data={"images": images})
    before = recipe.recipe_data

    assert dedupe_recipe_images(recipe) == []
    assert recipe.recipe_data is before
