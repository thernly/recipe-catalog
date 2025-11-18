"""Meal planning related Pydantic schemas."""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.core.security import sanitize_html


# ============================================
# Planned Meal Schemas
# ============================================


class PlannedMealBase(BaseModel):
    """Base planned meal schema."""

    recipe_id: int
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack|other)$")
    servings: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None


class PlannedMealCreate(PlannedMealBase):
    """Schema for creating a planned meal."""

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize notes field to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class PlannedMealUpdate(BaseModel):
    """Schema for updating a planned meal."""

    recipe_id: Optional[int] = None
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    meal_type: Optional[str] = Field(
        None, pattern="^(breakfast|lunch|dinner|snack|other)$"
    )
    servings: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize notes field to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_html(v)


class PlannedMeal(PlannedMealBase):
    """Full planned meal schema (response)."""

    id: int
    meal_plan_id: int
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
    planned_meals: List[PlannedMeal] = []

    model_config = ConfigDict(from_attributes=True)


class MealPlanSummary(MealPlanBase):
    """Simplified meal plan schema for listings."""

    id: int
    household_id: int
    created_at: datetime
    meal_count: int = 0

    model_config = ConfigDict(from_attributes=True)
