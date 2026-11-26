"""Shopping list related Pydantic schemas."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.security import sanitize_html
from app.services.aisles import guess_category


# ============================================
# Shopping List Item Schemas
# ============================================


class ShoppingListItemBase(BaseModel):
    """Base shopping list item schema."""

    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: str | None = Field(None, max_length=100)
    unit: str | None = Field(None, max_length=50)
    category: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=10000)
    checked: bool = False
    display_order: int = Field(0, ge=0, le=2**31 - 1)


class ShoppingListItemCreate(BaseModel):
    """Schema for creating a shopping list item."""

    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: str | None = Field(None, max_length=100)
    unit: str | None = Field(None, max_length=50)
    category: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=10000)

    @field_validator("item_name", "notes")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class ShoppingListItemUpdate(BaseModel):
    """Schema for updating a shopping list item."""

    item_name: str | None = Field(None, min_length=1, max_length=255)
    quantity: str | None = Field(None, max_length=100)
    unit: str | None = Field(None, max_length=50)
    category: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=10000)
    checked: bool | None = None
    display_order: int | None = Field(None, ge=0, le=2**31 - 1)

    @field_validator("item_name", "notes")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
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

    @model_validator(mode="after")
    def guess_missing_category(self) -> Self:
        """
        An item saved with no category is shown in a guessed one. Nothing is stored,
        so lists made before the guesser existed are grouped too, and a category the
        user picks always wins.
        """
        if not self.category:
            self.category = guess_category(self.item_name)
        return self


# ============================================
# Shopping List Schemas
# ============================================


class ShoppingListBase(BaseModel):
    """Base shopping list schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=10000)


class ShoppingListCreate(ShoppingListBase):
    """Schema for creating a shopping list."""

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
        """Sanitize text fields to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class ShoppingListUpdate(BaseModel):
    """Schema for updating a shopping list."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=10000)
    status: str | None = Field(None, pattern="^(active|archived)$")

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
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
    created_by_name: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[ShoppingListItem] = []

    model_config = ConfigDict(from_attributes=True)


class ShoppingListSummary(ShoppingListBase):
    """Simplified shopping list schema for listings."""

    id: int
    household_id: int
    status: str
    created_by_user_id: int
    created_by_name: str | None = None
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
    list_name: str | None = Field(None, max_length=255)
    servings: int | None = Field(None, ge=1)
    shopping_list_id: int | None = None  # add to this existing list instead of creating one
    ingredient_index: int | None = Field(None, ge=0)  # add only this recipeIngredient line


class GenerateFromMealPlanRequest(BaseModel):
    """Request schema for generating shopping list from meal plan."""

    meal_plan_id: int
    list_name: str | None = Field(None, max_length=255)
    selected_meal_ids: list[int] | None = Field(None, max_length=500)  # If None, use all meals
    shopping_list_id: int | None = None  # add to this existing list instead of creating one


class CategoryList(BaseModel):
    """Schema for category list response."""

    categories: list[str]
