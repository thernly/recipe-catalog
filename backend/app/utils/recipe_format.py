"""
Utilities for converting between internal recipe format and Schema.org Recipe JSON-LD format.
"""

import base64
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

import httpx

logger = logging.getLogger(__name__)


def convert_to_schema_org(recipe_db: Any) -> Dict[str, Any]:
    """
    Convert internal recipe format to Schema.org Recipe JSON-LD format.

    Args:
        recipe_db: Recipe database model instance

    Returns:
        Dict in Schema.org Recipe format with embedded base64 images
    """
    recipe_data = recipe_db.recipe_data or {}

    # Build the Schema.org format
    schema_recipe = {
        "name": recipe_db.name,
        "description": recipe_db.description or "",
        "image": _convert_images_to_schema(recipe_db.image_url),
        "author": recipe_data.get("author", []),
        "datePublished": recipe_data.get("datePublished") or (
            recipe_db.created_at.strftime("%Y-%m-%d") if recipe_db.created_at else ""
        ),
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


def convert_from_schema_org(schema_recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Schema.org Recipe JSON-LD format to internal recipe format.

    Args:
        schema_recipe: Dict in Schema.org Recipe format

    Returns:
        Dict with fields ready for RecipeCreate schema
    """
    # Extract first image URL if available
    image_url = None
    images = schema_recipe.get("image", [])
    if images and isinstance(images, list) and len(images) > 0:
        if isinstance(images[0], dict):
            image_url = images[0].get("url")
        elif isinstance(images[0], str):
            image_url = images[0]
    elif isinstance(images, str):
        image_url = images

    # Extract category and cuisine (take first if array)
    category = schema_recipe.get("recipeCategory")
    if isinstance(category, list) and len(category) > 0:
        category = category[0]

    cuisine = schema_recipe.get("recipeCuisine")
    if isinstance(cuisine, list) and len(cuisine) > 0:
        cuisine = cuisine[0]

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


def _convert_images_to_schema(image_url: Optional[str]) -> List[Dict[str, str]]:
    """
    Convert image URL to Schema.org image format with base64 data.

    Args:
        image_url: URL of the image

    Returns:
        List of image objects with URL, base64 data, and MIME type
    """
    if not image_url:
        return []

    images = []

    # Try to fetch and encode the image
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(image_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()

            # Get MIME type from headers
            content_type = response.headers.get('Content-Type', 'image/jpeg')

            # Encode to base64
            base64_data = base64.b64encode(response.content).decode('utf-8')

            images.append({
                "url": image_url,
                "data": base64_data,
                "mimeType": content_type
            })
    except (httpx.HTTPError, httpx.RequestError, ValueError) as e:
        # If image fetch fails, just include URL without data
        logger.warning(f"Failed to fetch image from {image_url}: {str(e)}")
        images.append({
            "url": image_url,
            "data": "",
            "mimeType": "image/jpeg"
        })
    except Exception as e:
        # Log unexpected errors during image conversion
        logger.exception(f"Unexpected error fetching image: {image_url}")
        images.append({
            "url": image_url,
            "data": "",
            "mimeType": "image/jpeg"
        })

    return images


def _ensure_array(value: Any) -> List[str]:
    """Convert value to array format."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value] if value else []
    return []


def _parse_duration_to_minutes(duration: str) -> Optional[int]:
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
    iso_pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?'
    match = re.match(iso_pattern, duration)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        return hours * 60 + minutes

    # Try simple format (30 minutes, 1 hour 30 minutes, etc.)
    total = 0

    # Extract hours
    hour_match = re.search(r'(\d+)\s*(?:hour|hr)s?', duration, re.IGNORECASE)
    if hour_match:
        total += int(hour_match.group(1)) * 60

    # Extract minutes
    min_match = re.search(r'(\d+)\s*(?:minute|min)s?', duration, re.IGNORECASE)
    if min_match:
        total += int(min_match.group(1))

    return total if total > 0 else None
