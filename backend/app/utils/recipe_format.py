"""
Utilities for converting between internal recipe format and Schema.org Recipe JSON-LD format.
"""

import base64
import logging
import re
from typing import Any

import httpx


logger = logging.getLogger(__name__)


def convert_to_schema_org(recipe_db: Any) -> dict[str, Any]:
    """
    Convert internal recipe format to Schema.org Recipe JSON-LD format.

    Args:
        recipe_db: Recipe database model instance

    Returns:
        Dict in Schema.org Recipe format with embedded base64 images
    """
    recipe_data = recipe_db.recipe_data or {}

    # Get stored images or fall back to fetching from URL
    stored_images = recipe_data.get("images", [])
    if stored_images:
        images = stored_images
    elif recipe_db.image_url:
        # Legacy support: fetch and encode if no stored images
        images = _convert_images_to_schema(recipe_db.image_url)
    else:
        images = []

    # Build the Schema.org format
    schema_recipe = {
        "name": recipe_db.name,
        "description": recipe_db.description or "",
        "image": images,
        "author": recipe_data.get("author", []),
        "datePublished": recipe_data.get("datePublished")
        or (recipe_db.created_at.strftime("%Y-%m-%d") if recipe_db.created_at else ""),
        "recipeYield": recipe_data.get("recipeYield", ""),
        "prepTime": recipe_data.get("prepTime", ""),
        "cookTime": recipe_data.get("cookTime", ""),
        "totalTime": recipe_data.get("totalTime", ""),
        "recipeCategory": _ensure_array(recipe_data.get("recipeCategory") or recipe_db.category),
        "recipeCuisine": _ensure_array(recipe_data.get("recipeCuisine") or recipe_db.cuisine),
        "keywords": recipe_data.get("keywords", ""),
        "recipeIngredient": recipe_data.get("recipeIngredient", []),
        "recipeInstructions": recipe_data.get("recipeInstructions", []),
        "equipment": recipe_data.get("equipment", []),
        "notes": recipe_data.get("notes", ""),
        "aggregateRating": recipe_data.get("aggregateRating", {}),
        "nutrition": recipe_data.get("nutrition", {}),
        "url": recipe_db.source_url or "",
    }

    return schema_recipe


def convert_from_schema_org(schema_recipe: dict[str, Any]) -> dict[str, Any]:
    """
    Convert Schema.org Recipe JSON-LD format to internal recipe format.

    Args:
        schema_recipe: Dict in Schema.org Recipe format

    Returns:
        Dict with fields ready for RecipeCreate schema
    """
    # Process images - extract and fetch base64 data if needed
    image_url = None
    images_data = []
    images = schema_recipe.get("image", [])

    # Normalize images to list format
    if isinstance(images, str):
        images = [images]
    elif not isinstance(images, list):
        images = []

    # Process each image
    for img in images:
        if isinstance(img, dict):
            # Image object with potential base64 data
            url = img.get("url", "")
            data = img.get("data", "")
            mime_type = img.get("mimeType", "image/jpeg")

            # If no base64 data but URL exists, fetch it
            if url and not data:
                fetched_image = _fetch_and_encode_image(url)
                if fetched_image:
                    images_data.append(fetched_image)
                else:
                    # Store without data if fetch fails
                    images_data.append({"url": url, "data": "", "mimeType": mime_type})
            else:
                # Store as-is
                images_data.append({"url": url, "data": data, "mimeType": mime_type})

            # Use first URL for image_url field
            if not image_url and url:
                image_url = url
        elif isinstance(img, str):
            # Just a URL string - fetch and encode it
            fetched_image = _fetch_and_encode_image(img)
            if fetched_image:
                images_data.append(fetched_image)
            else:
                # Store without data if fetch fails
                images_data.append({"url": img, "data": "", "mimeType": "image/jpeg"})

            # Use first URL for image_url field
            if not image_url:
                image_url = img

    # Extract category and cuisine (take first if array)
    category = schema_recipe.get("recipeCategory")
    if isinstance(category, list):
        category = category[0] if len(category) > 0 else None
    elif not category:
        category = None

    cuisine = schema_recipe.get("recipeCuisine")
    if isinstance(cuisine, list):
        cuisine = cuisine[0] if len(cuisine) > 0 else None
    elif not cuisine:
        cuisine = None

    # Calculate total time in minutes
    total_time_minutes = None
    total_time = schema_recipe.get("totalTime")
    if total_time:
        total_time_minutes = _parse_duration_to_minutes(total_time)
    elif schema_recipe.get("prepTime") or schema_recipe.get("cookTime"):
        prep_min = _parse_duration_to_minutes(schema_recipe.get("prepTime", ""))
        cook_min = _parse_duration_to_minutes(schema_recipe.get("cookTime", ""))
        total_time_minutes = (prep_min or 0) + (cook_min or 0) or None

    # Build recipe_data object (full recipe details)
    recipe_data = {
        "name": schema_recipe.get("name", ""),
        "author": schema_recipe.get("author", []),
        "datePublished": schema_recipe.get("datePublished", ""),
        "recipeYield": schema_recipe.get("recipeYield", ""),
        "prepTime": schema_recipe.get("prepTime", ""),
        "cookTime": schema_recipe.get("cookTime", ""),
        "totalTime": schema_recipe.get("totalTime", ""),
        "recipeCategory": schema_recipe.get("recipeCategory", []),
        "recipeCuisine": schema_recipe.get("recipeCuisine", []),
        "keywords": schema_recipe.get("keywords", ""),
        "recipeIngredient": schema_recipe.get("recipeIngredient", []),
        "recipeInstructions": schema_recipe.get("recipeInstructions", []),
        "equipment": schema_recipe.get("equipment", []),
        "notes": schema_recipe.get("notes", ""),
        "aggregateRating": schema_recipe.get("aggregateRating", {}),
        "nutrition": schema_recipe.get("nutrition", {}),
        "images": images_data,  # Store base64 image data
    }

    return {
        "name": schema_recipe.get("name", "Untitled Recipe"),
        "description": schema_recipe.get("description", ""),
        "image_url": image_url,
        "recipe_data": recipe_data,
        "source_url": schema_recipe.get("url", ""),
        "cuisine": cuisine,
        "category": category,
        "total_time_minutes": total_time_minutes,
        "source_type": "imported",
    }


def _fetch_and_encode_image(image_url: str) -> dict[str, str] | None:
    """
    Fetch an image from URL and encode it to base64.

    Args:
        image_url: URL of the image to fetch

    Returns:
        Dict with url, data (base64), and mimeType, or None if fetch fails
    """
    if not image_url:
        return None

    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(
                image_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            response.raise_for_status()

            # Get MIME type from headers
            content_type = response.headers.get("Content-Type", "image/jpeg")

            # Encode to base64
            base64_data = base64.b64encode(response.content).decode("utf-8")

            return {"url": image_url, "data": base64_data, "mimeType": content_type}
    except (httpx.HTTPError, httpx.RequestError, ValueError) as e:
        logger.warning(f"Failed to fetch image from {image_url}: {str(e)}")
        return None
    except Exception:
        logger.exception(f"Unexpected error fetching image: {image_url}")
        return None


def _convert_images_to_schema(image_url: str | None) -> list[dict[str, str]]:
    """
    Convert image URL to Schema.org image format with base64 data.
    Legacy function for backward compatibility.

    Args:
        image_url: URL of the image

    Returns:
        List of image objects with URL, base64 data, and MIME type
    """
    if not image_url:
        return []

    fetched = _fetch_and_encode_image(image_url)
    if fetched:
        return [fetched]

    # If fetch fails, return URL without data
    return [{"url": image_url, "data": "", "mimeType": "image/jpeg"}]


def _ensure_array(value: Any) -> list[str]:
    """Convert value to array format."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value] if value else []
    return []


def _parse_duration_to_minutes(duration: str) -> int | None:
    """
    Parse ISO 8601 duration or simple time string to minutes.

    Examples:
        "PT30M" -> 30
        "PT1H30M" -> 90
        "30 minutes" -> 30
        "1 hour 30 minutes" -> 90
    """
    if not duration:
        return None

    # Try ISO 8601 format (PT30M, PT1H30M, etc.)
    iso_pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?"
    match = re.match(iso_pattern, duration)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        return hours * 60 + minutes

    # Try simple format (30 minutes, 1 hour 30 minutes, etc.)
    total = 0

    # Extract hours
    hour_match = re.search(r"(\d+)\s*(?:hour|hr)s?", duration, re.IGNORECASE)
    if hour_match:
        total += int(hour_match.group(1)) * 60

    # Extract minutes
    min_match = re.search(r"(\d+)\s*(?:minute|min)s?", duration, re.IGNORECASE)
    if min_match:
        total += int(min_match.group(1))

    return total if total > 0 else None
