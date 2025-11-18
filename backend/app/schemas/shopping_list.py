"""Shopping list related Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.core.security import sanitize_html


# ============================================
# Shopping List Item Schemas
# ============================================


class ShoppingListItemBase(BaseModel):
    """Base shopping list item schema."""

    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    checked: bool = False
    display_order: int = 0


class ShoppingListItemCreate(BaseModel):
    """Schema for creating a shopping list item."""

    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

    @field_validator("item_name", "notes")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class ShoppingListItemUpdate(BaseModel):
    """Schema for updating a shopping list item."""

    item_name: Optional[str] = Field(None, min_length=1, max_length=255)
    quantity: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    checked: Optional[bool] = None
    display_order: Optional[int] = None

    @field_validator("item_name", "notes")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class ShoppingListItem(ShoppingListItemBase):
    """Full shopping list item schema (response)."""

    id: int
    list_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Shopping List Schemas
# ============================================


class ShoppingListBase(BaseModel):
    """Base shopping list schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ShoppingListCreate(ShoppingListBase):
    """Schema for creating a shopping list."""

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class ShoppingListUpdate(BaseModel):
    """Schema for updating a shopping list."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|archived)$")

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class ShoppingList(ShoppingListBase):
    """Full shopping list schema (response)."""

    id: int
    household_id: int
    status: str
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    items: List[ShoppingListItem] = []

    model_config = ConfigDict(from_attributes=True)


class ShoppingListSummary(ShoppingListBase):
    """Simplified shopping list schema for listings."""

    id: int
    household_id: int
    status: str
    created_at: datetime
    item_count: int = 0
    checked_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Special Request Schemas
# ============================================


class GenerateFromRecipeRequest(BaseModel):
    """Request schema for generating shopping list from recipe."""

    recipe_id: int
    list_name: Optional[str] = None
    servings: Optional[int] = Field(None, ge=1)


class GenerateFromMealPlanRequest(BaseModel):
    """Request schema for generating shopping list from meal plan."""

    meal_plan_id: int
    list_name: Optional[str] = None
    selected_meal_ids: Optional[List[int]] = None  # If None, use all meals


class CategoryList(BaseModel):
    """Schema for category list response."""

    categories: List[str]
