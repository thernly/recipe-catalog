"""
API v1 Router
All version 1 API endpoints.
"""

from fastapi import APIRouter

from app.api import (
    ai,
    auth,
    collections,
    export,
    households,
    import_recipes,
    meal_plans,
    oauth,
    recipes,
    shopping_lists,
    users,
)

# Create v1 router
api_v1_router = APIRouter(prefix="/api/v1")

# Include all routers under v1
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(oauth.router, prefix="/auth", tags=["OAuth"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(recipes.router, prefix="/recipes", tags=["Recipes"])
api_v1_router.include_router(collections.router, prefix="/collections", tags=["Collections"])
api_v1_router.include_router(export.router, prefix="/export", tags=["Export"])
api_v1_router.include_router(import_recipes.router, prefix="/import", tags=["Import"])
api_v1_router.include_router(households.router, prefix="/households", tags=["Households"])
api_v1_router.include_router(meal_plans.router, prefix="/meal-plans", tags=["Meal Plans"])
api_v1_router.include_router(
    shopping_lists.router, prefix="/shopping-lists", tags=["Shopping Lists"]
)
api_v1_router.include_router(ai.router, prefix="/ai", tags=["AI"])
