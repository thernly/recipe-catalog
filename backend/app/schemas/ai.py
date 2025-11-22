"""AI-related Pydantic schemas."""


from pydantic import BaseModel, Field


class AIRecipeGenerateRequest(BaseModel):
    """Schema for AI recipe generation request."""

    ingredients: list[str] = Field(..., min_length=1, description="List of available ingredients")
    cuisine: str | None = Field(None, max_length=100, description="Cuisine type")
    time_limit: int | None = Field(
        None, ge=1, le=480, description="Maximum cooking time in minutes"
    )
    dietary_preferences: list[str] | None = Field(
        default=None, description="Dietary preferences (e.g., vegetarian, vegan)"
    )
    equipment: list[str] | None = Field(default=None, description="Available kitchen equipment")


class AIRecipeGenerateResponse(BaseModel):
    """Schema for AI recipe generation response."""

    recipe: dict = Field(..., description="Generated recipe data")
    source_type: str = Field(default="ai-generated", description="Recipe source type")


class AIMenuGenerateRequest(BaseModel):
    """Schema for AI menu suggestion generation request."""

    days: int = Field(..., ge=1, le=14, description="Number of days for the menu")
    meals_per_day: list[str] = Field(
        ...,
        description="Meal types to include (e.g., ['breakfast', 'lunch', 'dinner'])",
    )
    dietary_preferences: list[str] | None = Field(
        default=None, description="Dietary preferences (e.g., vegetarian, vegan)"
    )
    cuisine: str | None = Field(None, max_length=100, description="Cuisine preference")
    mode: str = Field(
        "catalog-first",
        pattern="^(catalog-first|ai-only)$",
        description="Generation mode: catalog-first (use existing recipes) or ai-only (generate new suggestions)",
    )
    household_recipe_ids: list[int] | None = Field(
        default=None,
        description="Available recipe IDs from household catalog (for catalog-first mode)",
    )


class MealSuggestion(BaseModel):
    """Schema for a single meal suggestion."""

    day: int = Field(..., ge=1, description="Day number (1-indexed)")
    meal_type: str = Field(..., description="Meal type (breakfast, lunch, dinner, snack)")
    recipe_id: int | None = Field(
        None, description="Recipe ID from catalog (if mode is catalog-first)"
    )
    recipe_name: str = Field(..., description="Recipe name")
    description: str | None = Field(None, description="Brief description")
    prep_time: str | None = Field(None, description="Preparation time")
    cook_time: str | None = Field(None, description="Cooking time")


class AIMenuGenerateResponse(BaseModel):
    """Schema for AI menu suggestion generation response."""

    suggestions: list[MealSuggestion] = Field(..., description="List of meal suggestions")
    mode: str = Field(..., description="Generation mode used")
