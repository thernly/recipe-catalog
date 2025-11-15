"""Pydantic schemas for request/response validation."""

from app.schemas.user import (
    UserCreate,
    UserLogin,
    User,
    UserUpdate,
    PasswordChange,
    UserPreferences,
    UserPreferencesUpdate,
    Token,
    TokenData,
)
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    Recipe,
    RecipeSummary,
    RecipeImport,
    RecipeSearchParams,
    RecipeSearchResult,
)
from app.schemas.collection import (
    CollectionCreate,
    CollectionUpdate,
    Collection,
    CollectionWithCount,
    CollectionRecipeAdd,
    CollectionRecipeRemove,
)

__all__ = [
    # User
    "UserCreate",
    "UserLogin",
    "User",
    "UserUpdate",
    "PasswordChange",
    "UserPreferences",
    "UserPreferencesUpdate",
    "Token",
    "TokenData",
    # Recipe
    "RecipeCreate",
    "RecipeUpdate",
    "Recipe",
    "RecipeSummary",
    "RecipeImport",
    "RecipeSearchParams",
    "RecipeSearchResult",
    # Collection
    "CollectionCreate",
    "CollectionUpdate",
    "Collection",
    "CollectionWithCount",
    "CollectionRecipeAdd",
    "CollectionRecipeRemove",
]
