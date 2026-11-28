"""
AI-powered recipe generation API endpoints.
"""

from typing import Any

from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import and_, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.config import settings
from app.core.constants import MAX_RECIPES_IN_PROMPT
from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger
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


logger = get_logger(__name__)

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
            "ai_recipe_requested",
            user_id=current_user.id,
            ingredient_count=len(generation_request.ingredients),
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

    except AIServiceError:
        # The service has already classified and logged the provider failure.
        raise
    except (ValueError, TypeError) as exc:
        logger.exception(
            "ai_response_invalid_shape",
            operation="recipe",
            model=ai_service.model,
            user_id=current_user.id,
            error_type=type(exc).__name__,
        )
        raise AIServiceError("AI returned an invalid recipe. Please try again.") from exc
    except Exception as exc:
        logger.exception(
            "ai_request_failed", error_type=type(exc).__name__, user_id=current_user.id
        )
        raise AIServiceError("AI generation failed. Please try again.") from exc


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
        logger.info("ai_menu_requested", user_id=current_user.id, days=generation_request.days)

        # If catalog-first mode, fetch household recipes
        household_recipes: list[dict[str, Any]] | None = None
        if generation_request.mode == "catalog-first":
            catalog_query: Select[Any] = select(Recipe).where(
                and_(
                    Recipe.household_id == household.id,
                    Recipe.deleted_at.is_(None),
                )
            )
            if generation_request.household_recipe_ids is not None:
                catalog_query = catalog_query.where(
                    Recipe.id.in_(generation_request.household_recipe_ids)
                )
            result: Result[Any] = await db.execute(
                catalog_query.order_by(Recipe.id).limit(MAX_RECIPES_IN_PROMPT)
            )
            recipes = result.scalars().all()

            # Convert to dict format for AI service (the categories joined as one text)
            household_recipes = [
                {
                    "id": recipe.id,
                    "name": recipe.name,
                    "category": ", ".join(recipe.category_names) or None,
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

        allowed_ids = {entry["id"] for entry in household_recipes or []}
        if not isinstance(suggestions, list):
            raise ValueError("Invalid menu response")
        meal_suggestions = [MealSuggestion.model_validate(suggestion) for suggestion in suggestions]
        for suggestion in meal_suggestions:
            if suggestion.recipe_id not in allowed_ids:
                suggestion.recipe_id = None

        return AIMenuGenerateResponse(
            suggestions=meal_suggestions,
            mode=generation_request.mode,
        )

    except AIServiceError:
        # The service has already classified and logged the provider failure.
        raise
    except (ValueError, TypeError) as exc:
        logger.exception(
            "ai_response_invalid_shape",
            operation="menu",
            model=ai_service.model,
            user_id=current_user.id,
            error_type=type(exc).__name__,
        )
        raise AIServiceError("AI returned an invalid menu. Please try again.") from exc
    except Exception as exc:
        logger.exception(
            "ai_request_failed", error_type=type(exc).__name__, user_id=current_user.id
        )
        raise AIServiceError("AI generation failed. Please try again.") from exc
