"""Meal planning related Pydantic schemas."""

from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.security import sanitize_html


# ============================================
# Planned Meal Schemas
# ============================================


def _sanitize(value: str | None) -> str | None:
    """Sanitize notes to prevent XSS attacks."""
    return sanitize_html(value) if value is not None else None


def _title(value: str | None) -> str | None:
    """Sanitized like notes; a blank title is no title."""
    return (sanitize_html(value).strip() or None) if value is not None else None


class PlannedMealBase(BaseModel):
    """Base planned meal schema. A meal is a recipe, or free text in `title`
    ("Leftovers", "Eating out")."""

    recipe_id: int | None = None
    title: str | None = Field(None, max_length=200)
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack|other)$")
    servings: int | None = Field(None, ge=1)
    notes: str | None = Field(None, max_length=10000)


class PlannedMealCreate(PlannedMealBase):
    """Schema for creating a planned meal."""

    _sanitize_notes = field_validator("notes")(_sanitize)
    _clean_title = field_validator("title")(_title)

    @model_validator(mode="after")
    def recipe_or_title(self) -> Self:
        if (self.recipe_id is None) == (self.title is None):
            raise ValueError("Give a recipe or a title, not both")
        return self


class PlannedMealUpdate(BaseModel):
    """Schema for updating a planned meal. Giving `recipe_id` makes it a recipe meal
    and giving `title` makes it free text; the other one is cleared."""

    recipe_id: int | None = None
    title: str | None = Field(None, max_length=200)
    day_of_week: int | None = Field(None, ge=0, le=6)
    meal_type: str | None = Field(None, pattern="^(breakfast|lunch|dinner|snack|other)$")
    servings: int | None = Field(None, ge=1)
    notes: str | None = Field(None, max_length=10000)

    _sanitize_notes = field_validator("notes")(_sanitize)
    _clean_title = field_validator("title")(_title)

    @model_validator(mode="after")
    def not_both(self) -> Self:
        if self.recipe_id is not None and self.title is not None:
            raise ValueError("Give a recipe or a title, not both")
        return self


class PlannedMeal(PlannedMealBase):
    """Full planned meal schema (response)."""

    id: int
    meal_plan_id: int
    recipe_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Meal Plan Schemas
# ============================================


class MealPlanBase(BaseModel):
    """Base meal plan schema."""

    week_start_date: date


class MealPlanCreate(MealPlanBase):
    """Schema for creating a meal plan."""

    pass


class MealPlan(MealPlanBase):
    """Full meal plan schema (response)."""

    id: int
    household_id: int
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    planned_meals: list[PlannedMeal] = []

    model_config = ConfigDict(from_attributes=True)


class MealPlanSummary(MealPlanBase):
    """Simplified meal plan schema for listings."""

    id: int
    household_id: int
    created_at: datetime
    meal_count: int = 0

    model_config = ConfigDict(from_attributes=True)
