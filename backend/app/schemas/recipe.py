"""Recipe-related Pydantic schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.core.security import sanitize_html


# ============================================
# Recipe Schemas
# ============================================


class RecipeBase(BaseModel):
    """Base recipe schema."""

    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    image_url: Optional[str] = None
    recipe_data: Dict[str, Any]  # Full recipe JSON
    source_url: Optional[str] = None
    cuisine: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    total_time_minutes: Optional[int] = Field(None, ge=0)


class RecipeCreate(RecipeBase):
    """Schema for creating a recipe."""

    source_type: str = Field("manual", pattern="^(imported|manual|ai-generated)$")
    collection_ids: Optional[List[int]] = Field(default_factory=list)

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class RecipeUpdate(BaseModel):
    """Schema for updating a recipe."""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    image_url: Optional[str] = None
    recipe_data: Optional[Dict[str, Any]] = None
    cuisine: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    total_time_minutes: Optional[int] = Field(None, ge=0)
    collection_ids: Optional[List[int]] = None

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
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
    imported_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    # Creator information for household attribution
    creator_display_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecipeSummary(BaseModel):
    """Simplified recipe schema for listings."""

    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    cuisine: Optional[str] = None
    category: Optional[str] = None
    total_time_minutes: Optional[int] = None
    source_type: str
    created_at: datetime
    is_modified: bool
    # Creator information for household attribution
    creator_display_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecipeImport(BaseModel):
    """Schema for importing recipes from browser extension."""

    recipes: List[Dict[str, Any]]
    duplicate_handling: str = Field("skip", pattern="^(skip|update|create)$")
    collection_id: Optional[int] = None


# ============================================
# Recipe Search & Filter
# ============================================


class RecipeSearchParams(BaseModel):
    """Search and filter parameters."""

    query: Optional[str] = None
    cuisine: Optional[List[str]] = None
    category: Optional[List[str]] = None
    source_type: Optional[List[str]] = None
    collection_ids: Optional[List[int]] = None
    max_time_minutes: Optional[int] = None
    min_time_minutes: Optional[int] = None
    sort_by: str = Field(
        "recently_added",
        pattern="^(recently_added|alphabetical|time_asc|time_desc|recently_viewed)$",
    )
    page: int = Field(1, ge=1)
    per_page: int = Field(24, ge=1, le=100)


class RecipeSearchResult(BaseModel):
    """Recipe search results with pagination."""

    recipes: List[RecipeSummary]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
