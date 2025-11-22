"""Pydantic schemas for request/response validation."""

from app.schemas.collection import (
    Collection,
    CollectionCreate,
    CollectionRecipeAdd,
    CollectionRecipeRemove,
    CollectionUpdate,
    CollectionWithCount,
)
from app.schemas.oauth import (
    LinkedProviderResponse,
    OAuthCallbackRequest,
    ProviderInfo,
)
from app.schemas.recipe import (
    Recipe,
    RecipeCreate,
    RecipeImport,
    RecipeSearchParams,
    RecipeSearchResult,
    RecipeSummary,
    RecipeUpdate,
)
from app.schemas.shopping_list import (
    CategoryList,
    GenerateFromMealPlanRequest,
    GenerateFromRecipeRequest,
    ShoppingList,
    ShoppingListCreate,
    ShoppingListItem,
    ShoppingListItemCreate,
    ShoppingListItemUpdate,
    ShoppingListSummary,
    ShoppingListUpdate,
)
from app.schemas.user import (
    PasswordChange,
    Token,
    TokenData,
    User,
    UserCreate,
    UserLogin,
    UserPreferences,
    UserPreferencesUpdate,
    UserUpdate,
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
    # OAuth
    "ProviderInfo",
    "LinkedProviderResponse",
    "OAuthCallbackRequest",
    # Shopping List
    "ShoppingListCreate",
    "ShoppingListUpdate",
    "ShoppingList",
    "ShoppingListSummary",
    "ShoppingListItemCreate",
    "ShoppingListItemUpdate",
    "ShoppingListItem",
    "GenerateFromRecipeRequest",
    "GenerateFromMealPlanRequest",
    "CategoryList",
]
