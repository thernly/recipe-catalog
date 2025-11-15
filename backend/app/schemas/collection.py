"""Collection-related Pydantic schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


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
    pass


class CollectionUpdate(BaseModel):
    """Schema for updating a collection."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)


class Collection(CollectionBase):
    """Full collection schema (response)."""
    id: int
    user_id: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CollectionWithCount(Collection):
    """Collection with recipe count."""
    recipe_count: int


class CollectionRecipeAdd(BaseModel):
    """Schema for adding recipes to a collection."""
    recipe_ids: List[int] = Field(..., min_items=1)


class CollectionRecipeRemove(BaseModel):
    """Schema for removing recipes from a collection."""
    recipe_ids: List[int] = Field(..., min_items=1)
