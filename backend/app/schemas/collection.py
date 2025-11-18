"""Collection-related Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.core.security import sanitize_html


# ============================================
# Collection Schemas
# ============================================


class CollectionBase(BaseModel):
    """Base collection schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)


class CollectionCreate(CollectionBase):
    """Schema for creating a collection."""

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class CollectionUpdate(BaseModel):
    """Schema for updating a collection."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class Collection(CollectionBase):
    """Full collection schema (response)."""

    id: int
    user_id: int
    is_default: bool
    created_at: datetime
    updated_at: datetime
    # Creator information for household attribution
    creator_display_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CollectionWithCount(Collection):
    """Collection with recipe count."""

    recipe_count: int


class CollectionRecipeAdd(BaseModel):
    """Schema for adding recipes to a collection."""

    recipe_ids: List[int] = Field(..., min_length=1)


class CollectionRecipeRemove(BaseModel):
    """Schema for removing recipes from a collection."""

    recipe_ids: List[int] = Field(..., min_length=1)
