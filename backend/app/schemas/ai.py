"""AI-related Pydantic schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AIRecipeGenerateRequest(BaseModel):
    """Schema for AI recipe generation request."""

    ingredients: List[str] = Field(
        ..., min_length=1, description="List of available ingredients"
    )
    cuisine: Optional[str] = Field(None, max_length=100, description="Cuisine type")
    time_limit: Optional[int] = Field(
        None, ge=1, le=480, description="Maximum cooking time in minutes"
    )
    dietary_preferences: Optional[List[str]] = Field(
        default=None, description="Dietary preferences (e.g., vegetarian, vegan)"
    )
    equipment: Optional[List[str]] = Field(
        default=None, description="Available kitchen equipment"
    )


class AIRecipeGenerateResponse(BaseModel):
    """Schema for AI recipe generation response."""

    recipe: dict = Field(..., description="Generated recipe data")
    source_type: str = Field(default="ai-generated", description="Recipe source type")
