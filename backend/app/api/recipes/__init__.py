"""
Recipe API module.

This module combines CRUD, search, and export operations for recipes.
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .export import router as export_router
from .search import router as search_router


# Create main recipes router
router = APIRouter()

# Include sub-routers in order: specific paths first, then parameterized paths
# This ensures /search matches before /{recipe_id}
router.include_router(search_router, tags=["recipes"])
router.include_router(export_router, tags=["recipes"])
router.include_router(crud_router, tags=["recipes"])
