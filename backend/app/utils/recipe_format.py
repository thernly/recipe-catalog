"""
Utilities for converting between internal recipe format and Schema.org Recipe JSON-LD format.
"""

import base64
import html
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.constants import MAX_FETCHED_IMAGE_BYTES
from app.core.logging import get_logger
from app.core.security import sanitize_html
from app.models._utils import ensure_utc
from app.models.recipe_note import MAX_NOTE_LENGTH, note_author_name
from app.services.recipe_cleanup import parse_duration_minutes
from app.utils.safe_fetch import SafeFetchError, safe_fetch
from app.utils.urls import safe_http_url


logger = get_logger(__name__)

MAX_IMAGES = 5
MAX_IMPORTED_NOTES = 500


def plain_text(text: str) -> str:
    """Strip tags without entity-escaping, so "Mac & Cheese" stays as typed.

    The result is plain text (the frontend escapes on render), not HTML.
    """
    return html.unescape(sanitize_html(text)).strip()


async def convert_to_schema_org(recipe_db: Any, *, fetch_images: bool = True) -> dict[str, Any]:
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
    elif recipe_db.image_url and fetch_images:
        # Legacy support: fetch and encode if no stored images
        images = await _convert_images_to_schema(recipe_db.image_url)
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
        "comment": notes_to_schema(recipe_db),
    }

    return schema_recipe


def notes_to_schema(recipe_db: Any) -> list[dict[str, Any]]:
    """A recipe's notes as schema.org Comments, oldest first.

    Reads `recipe.notes` and each note's user, so ORM recipes must be loaded with
    load_recipe_notes() (async sessions cannot lazy-load).
    """
    return [
        {
            "@type": "Comment",
            "text": note.text,
            "dateCreated": ensure_utc(note.created_at).isoformat(),
            "author": {"@type": "Person", "name": note_author_name(note)},
        }
        for note in getattr(recipe_db, "notes", None) or []
    ]


def notes_from_schema(comments: Any) -> list[dict[str, Any]]:
    """Validate schema.org Comments from an imported file into note fields.

    Bad entries are dropped, never fatal. Returns dicts with `text`, `author_name`
    and `created_at` (aware UTC, or None when the file gives no usable date).
    """
    if isinstance(comments, dict):
        comments = [comments]
    if not isinstance(comments, list):
        return []
    notes: list[dict[str, Any]] = []
    for comment in comments:
        if len(notes) >= MAX_IMPORTED_NOTES:
            break
        if not isinstance(comment, dict) or not isinstance(comment.get("text"), str):
            continue
        text = plain_text(comment["text"])[:MAX_NOTE_LENGTH]
        if not text:
            continue
        author = comment.get("author")
        if isinstance(author, list):
            author = author[0] if author else None
        name = author.get("name") if isinstance(author, dict) else author
        name = plain_text(name)[:100] if isinstance(name, str) else ""
        notes.append(
            {
                "text": text,
                "author_name": name or "Unknown",
                "created_at": _parse_datetime(comment.get("dateCreated")),
            }
        )
    return notes


def _parse_datetime(value: Any) -> datetime | None:
    """An ISO 8601 string as an aware UTC datetime; None if missing or invalid."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    return ensure_utc(parsed).astimezone(UTC)


def comment_byline(comment: dict[str, Any]) -> str:
    """ "Sam, 2026-11-14 18:02 UTC" for a Comment made by notes_to_schema."""
    when = datetime.fromisoformat(comment["dateCreated"]).astimezone(UTC)
    return f"{comment['author']['name']}, {when:%Y-%m-%d %H:%M} UTC"


async def convert_from_schema_org(schema_recipe: dict[str, Any]) -> dict[str, Any]:
    """
    Convert Schema.org Recipe JSON-LD format to internal recipe format.

    Args:
        schema_recipe: Dict in Schema.org Recipe format

    Returns:
        Dict with fields ready for RecipeCreate schema
    """
    if not isinstance(schema_recipe, dict) or not isinstance(schema_recipe.get("name"), str):
        raise ValueError("Recipe name is required and must be text")
    # Bad optional fields are dropped, never fatal: one odd link or image must not
    # reject the whole recipe. Only http(s) links are kept (no javascript:/data:).
    source_url = safe_http_url(schema_recipe.get("url"))
    # Process images - extract and fetch base64 data if needed
    image_url = None
    images_data: list[dict[str, Any]] = []
    images = schema_recipe.get("image", [])

    # Normalize images to list format
    if isinstance(images, str):
        images = [images]
    elif not isinstance(images, list):
        images = []

    for img in images:
        if len(images_data) >= MAX_IMAGES:
            break
        if isinstance(img, dict):
            # Image object with potential base64 data
            url = safe_http_url(img.get("url")) or ""
            data = img.get("data") or ""
            mime_type = img.get("mimeType", "image/jpeg")
            if data and (
                not isinstance(data, str)
                or len(data) > (MAX_FETCHED_IMAGE_BYTES + 2) // 3 * 4
                or mime_type not in settings.ALLOWED_IMAGE_TYPES
            ):
                data = ""  # drop bad inline data; fall back to the URL, if any
            if not url and not data:
                continue
            if mime_type not in settings.ALLOWED_IMAGE_TYPES:
                mime_type = "image/jpeg"  # the fetch reports the real type

            # If no base64 data but URL exists, fetch it
            if url and not data:
                fetched_image = await _fetch_and_encode_image(url)
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
            if not safe_http_url(img):
                continue
            # Just a URL string - fetch and encode it
            fetched_image = await _fetch_and_encode_image(img)
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

    category = category[:100] if isinstance(category, str) else None
    cuisine = cuisine[:100] if isinstance(cuisine, str) else None

    # Calculate total time in minutes
    total_time_minutes = None
    total_time = schema_recipe.get("totalTime")
    if total_time:
        total_time_minutes = _parse_duration_to_minutes(total_time)
    elif schema_recipe.get("prepTime") or schema_recipe.get("cookTime"):
        prep_min = _parse_duration_to_minutes(schema_recipe.get("prepTime", ""))
        cook_min = _parse_duration_to_minutes(schema_recipe.get("cookTime", ""))
        total_time_minutes = (prep_min or 0) + (cook_min or 0) or None

    # Validate required fields
    recipe_name = plain_text(schema_recipe["name"])[:500]
    if not recipe_name:
        raise ValueError("Recipe name is required")

    # Build recipe_data object (full recipe details)
    recipe_data = {
        "name": recipe_name,
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
        "name": recipe_name,
        "description": plain_text(str(schema_recipe.get("description") or ""))[:10000],
        "image_url": image_url,
        "recipe_data": recipe_data,
        "source_url": source_url,
        "cuisine": cuisine,
        "category": category,
        "total_time_minutes": total_time_minutes,
        "source_type": "imported",
        # Restored as recipe notes by the importer; kept out of recipe_data
        "notes": notes_from_schema(schema_recipe.get("comment")),
    }


async def _fetch_and_encode_image(image_url: str | None) -> dict[str, str] | None:
    """
    Fetch an image from URL and encode it to base64.

    The fetch goes through `safe_fetch`, which refuses non-public addresses and caps
    size, redirects, time and content type.

    Args:
        image_url: URL of the image to fetch

    Returns:
        Dict with url, data (base64), and mimeType, or None if fetch fails
    """
    if not image_url:
        return None

    try:
        result = await safe_fetch(
            image_url,
            max_bytes=MAX_FETCHED_IMAGE_BYTES,
            allowed_content_types=settings.ALLOWED_IMAGE_TYPES,
        )
    except SafeFetchError as e:
        logger.warning("image_fetch_failed", url=image_url, reason=str(e))
        return None
    except Exception:
        logger.exception("image_fetch_unexpected_error", url=image_url)
        return None

    base64_data = base64.b64encode(result.content).decode("utf-8")
    return {"url": image_url, "data": base64_data, "mimeType": result.content_type}


async def _convert_images_to_schema(image_url: str | None) -> list[dict[str, str]]:
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

    fetched = await _fetch_and_encode_image(image_url)
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


def _parse_duration_to_minutes(duration: str | None) -> int | None:
    """Parse an ISO 8601 or prose duration to minutes (see `parse_duration_minutes`)."""
    return parse_duration_minutes(duration)
