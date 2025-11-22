"""Recipe-related Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import sanitize_html


# ============================================
# Recipe Schemas
# ============================================


class RecipeBase(BaseModel):
    """Base recipe schema."""

    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    image_url: str | None = None
    recipe_data: dict[str, Any]  # Full recipe JSON
    source_url: str | None = None
    cuisine: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=100)
    total_time_minutes: int | None = Field(None, ge=0)


class RecipeCreate(RecipeBase):
    """Schema for creating a recipe."""

    source_type: str = Field("manual", pattern="^(imported|manual|ai-generated)$")
    collection_ids: list[int] | None = Field(default_factory=list)

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class RecipeUpdate(BaseModel):
    """Schema for updating a recipe."""

    name: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    image_url: str | None = None
    recipe_data: dict[str, Any] | None = None
    cuisine: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=100)
    total_time_minutes: int | None = Field(None, ge=0)
    collection_ids: list[int] | None = None

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class Recipe(RecipeBase):
    """Full recipe schema (response)."""

    id: int
    user_id: int
    source_type: str
    is_modified: bool
    created_at: datetime
    updated_at: datetime
    imported_at: datetime | None = None
    deleted_at: datetime | None = None
    # Creator information for household attribution
    creator_display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RecipeSummary(BaseModel):
    """Simplified recipe schema for listings."""

    id: int
    name: str
    description: str | None = None
    image_url: str | None = None
    cuisine: str | None = None
    category: str | None = None
    total_time_minutes: int | None = None
    source_type: str
    created_at: datetime
    is_modified: bool
    # Creator information for household attribution
    creator_display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RecipeImport(BaseModel):
    """Schema for importing recipes from browser extension."""

    recipes: list[dict[str, Any]]
    duplicate_handling: str = Field("skip", pattern="^(skip|update|create)$")
    collection_id: int | None = None


# ============================================
# Recipe Search & Filter
# ============================================


class RecipeSearchParams(BaseModel):
    """Search and filter parameters."""

    query: str | None = None
    cuisine: list[str] | None = None
    category: list[str] | None = None
    source_type: list[str] | None = None
    collection_ids: list[int] | None = None
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
