"""
AI-powered recipe generation API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.ai import AIRecipeGenerateRequest, AIRecipeGenerateResponse
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

        return AIRecipeGenerateResponse(
            recipe=recipe_data, source_type="ai-generated"
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
        logger.error(f"AI generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
