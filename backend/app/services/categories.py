"""A recipe's categories: the only place that writes them.

The rows in `recipe_categories` are the filter index; `recipe_data["recipeCategory"]`
is the schema.org copy. `set_categories` writes both so they never drift apart.
"""

import re
from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_CATEGORIES
from app.models.recipe import Recipe
from app.models.recipe_category import RecipeCategory
from app.models.user import UserPreferences


MAX_CATEGORIES = 20
MAX_CATEGORY_LENGTH = 100
_SEPARATORS = re.compile(r"[,;]")


def normalize_categories(names: Iterable[Any], known: Iterable[str] = ()) -> list[str]:
    """Clean a list of category names as typed or imported.

    Entries are split on "," and ";", stripped, cut to 100 characters, blanks dropped,
    and duplicates removed case-insensitively (first spelling wins). An entry that
    matches a known option case-insensitively takes the known spelling, so
    "main course" lands under "Main Course" rather than under "Other". At most 20.
    """
    canonical = {option.lower(): option for option in known}
    result: list[str] = []
    seen: set[str] = set()
    for entry in names:
        if not isinstance(entry, str):
            continue
        for part in _SEPARATORS.split(entry):
            name = part.strip()[:MAX_CATEGORY_LENGTH].strip()
            if not name:
                continue
            name = canonical.get(name.lower(), name)
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            result.append(name)
            if len(result) == MAX_CATEGORIES:
                return result
    return result


def set_categories(recipe: Recipe, names: list[str]) -> None:
    """Replace the recipe's category rows and the schema.org list in its JSON.

    Pass names through normalize_categories first. Categories the recipe already has
    keep their place and new ones follow, in both the rows and the JSON. A new dict is
    assigned to recipe_data so SQLAlchemy notices the JSON change.
    """
    # Recipe still uses legacy Column attributes, which mypy types as Column[Any]
    row: Any = recipe
    # Keep the rows whose name stays: SQLAlchemy inserts new rows before it deletes
    # the orphans, so a fresh row for an unchanged name would hit the unique constraint
    wanted = set(names)
    kept = [category for category in row.categories if str(category.name) in wanted]
    kept_names = {str(category.name) for category in kept}
    row.categories = kept + [RecipeCategory(name=name) for name in names if name not in kept_names]
    data = row.recipe_data if isinstance(row.recipe_data, dict) else {}
    row.recipe_data = {**data, "recipeCategory": row.category_names}


async def known_categories(user_id: int, db: AsyncSession) -> list[str]:
    """The standard categories plus the user's own: the spellings to normalize to."""
    prefs = (
        await db.execute(select(UserPreferences).where(UserPreferences.user_id == user_id))
    ).scalar_one_or_none()
    custom: list[Any] = (
        prefs.custom_categories if prefs and isinstance(prefs.custom_categories, list) else []
    )
    return DEFAULT_CATEGORIES + [str(name) for name in custom]
