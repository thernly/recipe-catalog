"""
AI-powered recipe generation API endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.models.household import Household
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.ai import (
    AIMenuGenerateRequest,
    AIMenuGenerateResponse,
    AIRecipeGenerateRequest,
    AIRecipeGenerateResponse,
    MealSuggestion,
)
from app.services.ai import ai_service


logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/generate-recipe",
    response_model=AIRecipeGenerateResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(f"{settings.AI_RATE_LIMIT_PER_HOUR}/hour")
async def generate_recipe(
    request: Request,
    generation_request: AIRecipeGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a recipe from ingredients using AI.

    This endpoint uses AI to create a recipe based on provided ingredients
    and optional constraints like cuisine type, time limit, and dietary preferences.

    Args:
        request: The FastAPI request object (for rate limiting)
        generation_request: Recipe generation parameters
        current_user: The authenticated user

    Returns:
        AIRecipeGenerateResponse: Generated recipe data

    Raises:
        HTTPException: If AI generation fails or rate limit is exceeded
    """
    try:
        logger.info(
            f"AI recipe generation requested by user {current_user.id} with {len(generation_request.ingredients)} ingredients"
        )

        # Generate recipe using AI service
        recipe_data = await ai_service.generate_recipe(
            ingredients=generation_request.ingredients,
            cuisine=generation_request.cuisine,
            time_limit=generation_request.time_limit,
            dietary_preferences=generation_request.dietary_preferences,
            equipment=generation_request.equipment,
        )

        return AIRecipeGenerateResponse(recipe=recipe_data, source_type="ai-generated")

    except ValueError as e:
        # Configuration error
        logger.error(f"AI configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        # AI generation error
        logger.error(f"AI generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/generate-menu",
    response_model=AIMenuGenerateResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(f"{settings.AI_RATE_LIMIT_PER_HOUR}/hour")
async def generate_menu(
    request: Request,
    generation_request: AIMenuGenerateRequest,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate menu suggestions for multiple days using AI.

    This endpoint uses AI to create a menu plan based on the number of days,
    meal types, and optional dietary preferences and cuisine.

    Args:
        request: The FastAPI request object (for rate limiting)
        generation_request: Menu generation parameters
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        AIMenuGenerateResponse: Generated menu suggestions

    Raises:
        HTTPException: If AI generation fails or rate limit is exceeded
    """
    try:
        logger.info(
            f"AI menu generation requested by user {current_user.id} for {generation_request.days} days"
        )

        # If catalog-first mode, fetch household recipes
        household_recipes = None
        if generation_request.mode == "catalog-first":
            result = await db.execute(
                select(Recipe).where(
                    and_(
                        Recipe.household_id == household.id,
                        Recipe.deleted_at.is_(None),
                    )
                )
            )
            recipes = result.scalars().all()

            # Convert to dict format for AI service
            household_recipes = [
                {
                    "id": recipe.id,
                    "name": recipe.name,
                    "category": recipe.recipeCategory[0] if recipe.recipeCategory else None,
                }
                for recipe in recipes
            ]

        # Generate menu using AI service
        suggestions = await ai_service.generate_menu(
            days=generation_request.days,
            meals_per_day=generation_request.meals_per_day,
            dietary_preferences=generation_request.dietary_preferences,
            cuisine=generation_request.cuisine,
            mode=generation_request.mode,
            household_recipes=household_recipes,
        )

        # Convert to MealSuggestion objects
        meal_suggestions = [MealSuggestion(**suggestion) for suggestion in suggestions]

        return AIMenuGenerateResponse(
            suggestions=meal_suggestions,
            mode=generation_request.mode,
        )

    except ValueError as e:
        # Configuration error
        logger.error(f"AI configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        # AI generation error
        logger.error(f"AI menu generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
