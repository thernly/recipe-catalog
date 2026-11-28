"""Recipe-related Pydantic schemas."""

import html
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import sanitize_html
from app.utils.urls import safe_http_url, validate_http_url


# ============================================
# Recipe Schemas
# ============================================


class RecipeBase(BaseModel):
    """Base recipe schema."""

    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=10000)
    image_url: str | None = Field(None, max_length=2048)
    recipe_data: dict[str, Any]  # Full recipe JSON
    source_url: str | None = Field(None, max_length=2048)

    _validate_urls = field_validator("source_url", "image_url")(validate_http_url)
    cuisine: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=100)
    total_time_minutes: int | None = Field(None, ge=0)


class RecipeCreate(RecipeBase):
    """Schema for creating a recipe."""

    source_type: str = Field("manual", pattern="^(imported|manual|ai-generated)$")
    collection_ids: list[int] | None = Field(default_factory=list, max_length=500)

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
        """Strip markup; store plain text (the frontend escapes on render)."""
        if v is None:
            return v
        return html.unescape(sanitize_html(v))


class RecipeUpdate(BaseModel):
    """Schema for updating a recipe."""

    name: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, max_length=10000)
    image_url: str | None = Field(None, max_length=2048)
    source_url: str | None = Field(None, max_length=2048)  # null clears it
    _validate_urls = field_validator("source_url", "image_url")(validate_http_url)

    recipe_data: dict[str, Any] | None = None
    cuisine: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=100)
    total_time_minutes: int | None = Field(None, ge=0)
    collection_ids: list[int] | None = Field(None, max_length=500)

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
        """Strip markup; store plain text (the frontend escapes on render)."""
        if v is None:
            return v
        return html.unescape(sanitize_html(v))


class Recipe(RecipeBase):
    """Full recipe schema (response).

    Serializes stored rows, so the input limits from RecipeBase are lifted: a value
    stored before a limit existed (or by import) must never 500 a read.
    """

    name: str
    description: str | None = None
    image_url: str | None = None
    source_url: str | None = None
    cuisine: str | None = None
    category: str | None = None
    total_time_minutes: int | None = None
    _validate_urls = field_validator("source_url", "image_url", mode="before")(safe_http_url)

    id: int
    user_id: int
    source_type: str
    is_modified: bool
    created_at: datetime
    updated_at: datetime
    imported_at: datetime | None = None
    deleted_at: datetime | None = None
    rating: int | None = None
    last_cooked_on: date | None = None
    # Creator information for household attribution
    creator_display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RecipeCooking(BaseModel):
    """A recipe's household rating and last-cooked date. A field left out of a
    request is not changed; null clears it."""

    rating: int | None = Field(None, ge=1, le=5)
    last_cooked_on: date | None = None


class RecipeSummary(BaseModel):
    """Simplified recipe schema for listings."""

    id: int
    # Owner: only they may edit or delete, so clients need it to offer the right actions
    user_id: int
    name: str
    description: str | None = None
    image_url: str | None = None
    _validate_image = field_validator("image_url", mode="before")(safe_http_url)
    # Stored photo served by GET /recipes/{id}/photo; image_url is only the fallback
    has_photo: bool = False
    cuisine: str | None = None
    category: str | None = None
    total_time_minutes: int | None = None
    source_type: str
    created_at: datetime
    is_modified: bool
    rating: int | None = None
    last_cooked_on: date | None = None
    # Creator information for household attribution
    creator_display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RecipeImport(BaseModel):
    """Schema for importing recipes from browser extension."""

    recipes: list[dict[str, Any]] = Field(..., max_length=500)
    duplicate_handling: str = Field("skip", pattern="^(skip|update|create)$")
    collection_id: int | None = None


# ============================================
# Recipe Search & Filter
# ============================================


class RecipeSearchParams(BaseModel):
    """Search and filter parameters."""

    query: str | None = Field(None, max_length=500)
    cuisine: list[str] | None = Field(None, max_length=100)
    category: list[str] | None = Field(None, max_length=100)
    source_type: list[str] | None = Field(None, max_length=3)
    collection_ids: list[int] | None = Field(None, max_length=500)
    max_time_minutes: int | None = None
    min_time_minutes: int | None = None
    sort_by: str = Field(
        "recently_added",
        pattern="^(recently_added|alphabetical|time_asc|time_desc|recently_viewed)$",
    )
    page: int = Field(1, ge=1)
    per_page: int = Field(24, ge=1, le=100)


class RecipeSearchResult(BaseModel):
    """Recipe search results with pagination."""

    recipes: list[RecipeSummary]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
