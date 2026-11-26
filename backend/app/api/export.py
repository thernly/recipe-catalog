"""
Export API endpoints
Allows users to export their recipe data in various formats
"""

import json
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.models.collection import Collection, RecipeCollection
from app.models.household import Household
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.recipe_note import load_recipe_notes
from app.models.shopping_list import ShoppingList
from app.models.user import User, UserPreferences
from app.services.recipe_export import cooking_note_lines
from app.utils.recipe_format import convert_to_schema_org, notes_to_schema


router = APIRouter()

ExportScope = Literal["mine", "household"]


async def _recipes_to_export(
    db: AsyncSession, current_user: User, household: Household, scope: ExportScope
) -> list[Recipe]:
    """The caller's own recipes, or (a read, so household-scoped) everyone's in the household."""
    owner_or_household: ColumnElement[bool] = (
        Recipe.household_id == household.id
        if scope == "household"
        else Recipe.user_id == current_user.id
    )
    result = await db.execute(
        select(Recipe)
        .where(owner_or_household)
        .where(Recipe.deleted_at.is_(None))
        .order_by(Recipe.created_at.desc())
        .options(load_recipe_notes())
    )
    return list(result.scalars().all())


@router.get("/recipes")
async def export_recipes(
    format: Literal["json", "markdown", "text"] = "json",
    scope: ExportScope = "mine",
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Export recipes in the specified format.

    Scope:
    - mine (default): recipes the caller added
    - household: every recipe in the caller's household

    Formats:
    - json: Complete recipe data in JSON format
    - markdown: Human-readable markdown format
    - text: Plain text format
    """
    recipes = await _recipes_to_export(db, current_user, household, scope)

    if format == "json":
        # Export as JSON in Schema.org Recipe format
        recipes_schema_org = [await convert_to_schema_org(recipe) for recipe in recipes]

        # Return as downloadable JSON file
        # Export as array of recipes (not wrapped in object)
        return Response(
            content=json.dumps(recipes_schema_org, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="recipes_export_{datetime.now(UTC).strftime("%Y%m%d")}.json"'
            },
        )

    elif format == "markdown":
        # Export as Markdown with comprehensive information
        lines = [
            f"# Recipe Export - {current_user.display_name}",
            f"\nExported: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"\nTotal Recipes: {len(recipes)}",
            "\n---\n",
        ]

        for recipe in recipes:
            # Convert to schema.org format to get all fields
            schema_recipe = await convert_to_schema_org(recipe)

            lines.append(f"# {schema_recipe['name']}\n")

            if schema_recipe.get("description"):
                lines.append(f"{schema_recipe['description']}\n")

            # Metadata section
            metadata_items = []
            if schema_recipe.get("datePublished"):
                metadata_items.append(f"**Date Published:** {schema_recipe['datePublished']}")
            if schema_recipe.get("recipeYield"):
                metadata_items.append(f"**Yield:** {schema_recipe['recipeYield']}")
            if schema_recipe.get("prepTime"):
                metadata_items.append(f"**Prep Time:** {schema_recipe['prepTime']}")
            if schema_recipe.get("cookTime"):
                metadata_items.append(f"**Cook Time:** {schema_recipe['cookTime']}")
            if schema_recipe.get("totalTime"):
                metadata_items.append(f"**Total Time:** {schema_recipe['totalTime']}")
            if schema_recipe.get("recipeCategory"):
                categories = schema_recipe["recipeCategory"]
                category_str = (
                    ", ".join(categories) if isinstance(categories, list) else str(categories)
                )
                metadata_items.append(f"**Category:** {category_str}")
            if schema_recipe.get("recipeCuisine"):
                cuisines = schema_recipe["recipeCuisine"]
                cuisine_str = ", ".join(cuisines) if isinstance(cuisines, list) else str(cuisines)
                metadata_items.append(f"**Cuisine:** {cuisine_str}")
            if schema_recipe.get("keywords"):
                metadata_items.append(f"**Keywords:** {schema_recipe['keywords']}")
            if schema_recipe.get("url"):
                metadata_items.append(f"**Source:** {schema_recipe['url']}")

            if metadata_items:
                lines.append("")
                lines.extend(metadata_items)

            # Rating
            if schema_recipe.get("aggregateRating"):
                rating = schema_recipe["aggregateRating"]
                if isinstance(rating, dict) and rating.get("ratingValue"):
                    rating_text = f"**Rating:** {rating['ratingValue']}"
                    if rating.get("ratingCount"):
                        rating_text += f" / 5 ({rating['ratingCount']} ratings)"
                    lines.append(f"\n{rating_text}\n")

            # Ingredients
            if schema_recipe.get("recipeIngredient"):
                lines.append("\n## Ingredients")
                for ingredient in schema_recipe["recipeIngredient"]:
                    lines.append(f"- {ingredient}")

            # Equipment
            if schema_recipe.get("equipment"):
                lines.append("\n## Equipment")
                equipment = schema_recipe["equipment"]
                if isinstance(equipment, list):
                    for item in equipment:
                        lines.append(f"- {item}")
                elif isinstance(equipment, str):
                    lines.append(f"- {equipment}")

            # Instructions
            if schema_recipe.get("recipeInstructions"):
                lines.append("\n## Instructions")
                instructions = schema_recipe["recipeInstructions"]
                if isinstance(instructions, list):
                    for i, step in enumerate(instructions, 1):
                        if isinstance(step, dict):
                            step_text = step.get("text", str(step))
                        else:
                            step_text = str(step)
                        lines.append(f"{i}. {step_text}")
                elif isinstance(instructions, str):
                    lines.append(instructions)

            # Notes
            if schema_recipe.get("notes"):
                lines.append("\n## Recipe Notes\n")
                lines.append(schema_recipe["notes"])
            lines.extend(cooking_note_lines(schema_recipe, markdown=True))

            # Nutrition
            if schema_recipe.get("nutrition"):
                nutrition = schema_recipe["nutrition"]
                if isinstance(nutrition, dict) and nutrition:
                    lines.append("\n## Nutrition Information\n")
                    for key, value in nutrition.items():
                        if value:
                            # Convert camelCase to Title Case
                            label = (
                                "".join([" " + c if c.isupper() else c for c in key])
                                .strip()
                                .title()
                            )
                            lines.append(f"- **{label}:** {value}")

            # Images
            if schema_recipe.get("image"):
                images = schema_recipe["image"]
                if isinstance(images, list) and images:
                    lines.append("\n")
                    for idx, img in enumerate(images, 1):
                        if isinstance(img, dict):
                            if img.get("data"):
                                mime_type = img.get("mimeType", "image/jpeg")
                                lines.append(
                                    f"![Recipe Image {idx}](data:{mime_type};base64,{img['data']})"
                                )
                            elif img.get("url"):
                                lines.append(f"![Recipe Image {idx}]({img['url']})")

            lines.append("\n---\n")

        content = "\n".join(lines)

        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="recipes_export_{datetime.now(UTC).strftime("%Y%m%d")}.md"'
            },
        )

    elif format == "text":
        # Export as plain text with comprehensive information
        lines = [
            f"RECIPE EXPORT - {current_user.display_name}",
            f"Exported: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Total Recipes: {len(recipes)}",
            "\n" + "=" * 80 + "\n",
        ]

        for recipe in recipes:
            # Convert to schema.org format to get all fields
            schema_recipe = await convert_to_schema_org(recipe)

            lines.append(f"\n{schema_recipe['name'].upper()}")
            lines.append("=" * len(schema_recipe["name"]))

            if schema_recipe.get("description"):
                lines.append(f"\n{schema_recipe['description']}\n")

            # Metadata section
            if schema_recipe.get("datePublished"):
                lines.append(f"Date Published: {schema_recipe['datePublished']}")
            if schema_recipe.get("recipeYield"):
                lines.append(f"Yield: {schema_recipe['recipeYield']}")
            if schema_recipe.get("prepTime"):
                lines.append(f"Prep Time: {schema_recipe['prepTime']}")
            if schema_recipe.get("cookTime"):
                lines.append(f"Cook Time: {schema_recipe['cookTime']}")
            if schema_recipe.get("totalTime"):
                lines.append(f"Total Time: {schema_recipe['totalTime']}")
            if schema_recipe.get("recipeCategory"):
                categories = schema_recipe["recipeCategory"]
                category_str = (
                    ", ".join(categories) if isinstance(categories, list) else str(categories)
                )
                lines.append(f"Category: {category_str}")
            if schema_recipe.get("recipeCuisine"):
                cuisines = schema_recipe["recipeCuisine"]
                cuisine_str = ", ".join(cuisines) if isinstance(cuisines, list) else str(cuisines)
                lines.append(f"Cuisine: {cuisine_str}")
            if schema_recipe.get("keywords"):
                lines.append(f"Keywords: {schema_recipe['keywords']}")
            if schema_recipe.get("url"):
                lines.append(f"Source: {schema_recipe['url']}")

            # Rating
            if schema_recipe.get("aggregateRating"):
                rating = schema_recipe["aggregateRating"]
                if isinstance(rating, dict) and rating.get("ratingValue"):
                    rating_text = f"Rating: {rating['ratingValue']}"
                    if rating.get("ratingCount"):
                        rating_text += f" / 5 ({rating['ratingCount']} ratings)"
                    lines.append(f"\n{rating_text}")

            # Ingredients
            if schema_recipe.get("recipeIngredient"):
                lines.append("\nINGREDIENTS:")
                for ingredient in schema_recipe["recipeIngredient"]:
                    lines.append(f"  - {ingredient}")

            # Equipment
            if schema_recipe.get("equipment"):
                lines.append("\nEQUIPMENT:")
                equipment = schema_recipe["equipment"]
                if isinstance(equipment, list):
                    for item in equipment:
                        lines.append(f"  - {item}")
                elif isinstance(equipment, str):
                    lines.append(f"  - {equipment}")

            # Instructions
            if schema_recipe.get("recipeInstructions"):
                lines.append("\nINSTRUCTIONS:")
                instructions = schema_recipe["recipeInstructions"]
                if isinstance(instructions, list):
                    for i, step in enumerate(instructions, 1):
                        if isinstance(step, dict):
                            step_text = step.get("text", str(step))
                        else:
                            step_text = str(step)
                        lines.append(f"  {i}. {step_text}")
                elif isinstance(instructions, str):
                    lines.append(f"  {instructions}")

            # Notes
            if schema_recipe.get("notes"):
                lines.append("\nRECIPE NOTES:")
                lines.append(f"  {schema_recipe['notes']}")
            lines.extend(cooking_note_lines(schema_recipe, markdown=False))

            # Nutrition
            if schema_recipe.get("nutrition"):
                nutrition = schema_recipe["nutrition"]
                if isinstance(nutrition, dict) and nutrition:
                    lines.append("\nNUTRITION INFORMATION:")
                    for key, value in nutrition.items():
                        if value:
                            # Convert camelCase to Title Case
                            label = (
                                "".join([" " + c if c.isupper() else c for c in key])
                                .strip()
                                .title()
                            )
                            lines.append(f"  {label}: {value}")

            # Images (just URLs for text format)
            if schema_recipe.get("image"):
                images = schema_recipe["image"]
                if isinstance(images, list) and images:
                    lines.append("\nIMAGES:")
                    for idx, img in enumerate(images, 1):
                        if isinstance(img, dict) and img.get("url"):
                            lines.append(f"  {idx}. {img['url']}")

            lines.append("\n" + "=" * 80 + "\n")

        content = "\n".join(lines)

        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="recipes_export_{datetime.now(UTC).strftime("%Y%m%d")}.txt"'
            },
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid export format")


@router.get("/collections")
async def export_collections(
    format: Literal["json", "markdown", "text"] = "json",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export all user collections with their recipes.
    """
    # Fetch all user collections
    result = await db.execute(
        select(Collection)
        .where(Collection.user_id == current_user.id)
        .order_by(Collection.created_at.desc())
    )
    collections = result.scalars().all()

    if format == "json":
        # Export as JSON
        export_data = {
            "export_date": datetime.now(UTC).isoformat(),
            "user": {
                "email": current_user.email,
                "display_name": current_user.display_name,
            },
            "total_collections": len(collections),
            "collections": [],
        }

        for collection in collections:
            # Get recipes in this collection
            recipe_result = await db.execute(
                select(Recipe)
                .join(RecipeCollection, Recipe.id == RecipeCollection.recipe_id)
                .where(RecipeCollection.collection_id == collection.id)
                .where(Recipe.deleted_at.is_(None))
            )
            recipes = recipe_result.scalars().all()

            export_data["collections"].append(
                {
                    "id": collection.id,
                    "name": collection.name,
                    "description": collection.description,
                    "created_at": collection.created_at.isoformat()
                    if collection.created_at
                    else None,
                    "recipe_count": len(recipes),
                    "recipes": [
                        {
                            "id": recipe.id,
                            "name": recipe.name,
                            "description": recipe.description,
                        }
                        for recipe in recipes
                    ],
                }
            )

        return Response(
            content=json.dumps(export_data, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="collections_export_{datetime.now(UTC).strftime("%Y%m%d")}.json"'
            },
        )

    elif format == "markdown":
        # Export as Markdown
        lines = [
            f"# Collections Export - {current_user.display_name}",
            f"\nExported: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"\nTotal Collections: {len(collections)}",
            "\n---\n",
        ]

        for collection in collections:
            # Get recipes in this collection
            recipe_result = await db.execute(
                select(Recipe)
                .join(RecipeCollection, Recipe.id == RecipeCollection.recipe_id)
                .where(RecipeCollection.collection_id == collection.id)
                .where(Recipe.deleted_at.is_(None))
            )
            recipes = recipe_result.scalars().all()

            lines.append(f"\n## {collection.name}\n")

            if collection.description:
                lines.append(f"{collection.description}\n")

            lines.append(f"\n**Recipe Count:** {len(recipes)}\n")

            if recipes:
                lines.append("### Recipes:\n")
                for recipe in recipes:
                    lines.append(f"- {recipe.name}")

            lines.append("\n---\n")

        content = "\n".join(lines)

        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="collections_export_{datetime.now(UTC).strftime("%Y%m%d")}.md"'
            },
        )

    else:
        raise HTTPException(status_code=400, detail="Format not supported for collections")


@router.get("/all")
async def export_all_data(
    scope: ExportScope = "mine",
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Export a Complete Backup as JSON: the user's recipes, collections and preferences,
    plus the household's meal plans and shopping lists. `scope=household` includes
    every household member's recipes instead of only the caller's.

    `POST /import/backup` restores it. Recipe ids in `collections[].recipe_ids` and
    `meal_plans[].meals[].recipe_id` refer to `recipes[].id` in the same file.
    """
    recipes = await _recipes_to_export(db, current_user, household, scope)

    # Fetch collections
    collection_result = await db.execute(
        select(Collection)
        .where(Collection.user_id == current_user.id)
        .order_by(Collection.created_at.desc())
    )
    collections = collection_result.scalars().all()

    # Fetch user preferences explicitly
    preferences_result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    user_preferences = preferences_result.scalar_one_or_none()

    # Build complete export
    export_data = {
        "export_date": datetime.now(UTC).isoformat(),
        "export_type": "complete_backup",
        "user": {
            "email": current_user.email,
            "display_name": current_user.display_name,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "preferences": {
            "theme": user_preferences.theme if user_preferences else "classic",
            "default_view": user_preferences.default_view if user_preferences else "grid",
            "default_sort": user_preferences.default_sort if user_preferences else "recently_added",
        }
        if user_preferences
        else None,
        "statistics": {
            "total_recipes": len(recipes),
            "total_collections": len(collections),
        },
        "recipes": [
            {
                "id": recipe.id,
                "name": recipe.name,
                "description": recipe.description,
                "image_url": recipe.image_url,
                "recipe_data": recipe.recipe_data,
                "source_url": recipe.source_url,
                "source_type": recipe.source_type,
                "cuisine": recipe.cuisine,
                "category": recipe.category,
                "total_time_minutes": recipe.total_time_minutes,
                "created_at": recipe.created_at.isoformat() if recipe.created_at else None,
                "updated_at": recipe.updated_at.isoformat() if recipe.updated_at else None,
                "rating": recipe.rating,
                "last_cooked_on": (
                    recipe.last_cooked_on.isoformat() if recipe.last_cooked_on else None
                ),
                "comment": notes_to_schema(recipe),
            }
            for recipe in recipes
        ],
        "collections": [],
    }

    # Add collections with their recipes
    for collection in collections:
        recipe_result = await db.execute(
            select(Recipe)
            .join(RecipeCollection, Recipe.id == RecipeCollection.recipe_id)
            .where(RecipeCollection.collection_id == collection.id)
            .where(Recipe.deleted_at.is_(None))
        )
        coll_recipes = recipe_result.scalars().all()

        export_data["collections"].append(
            {
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "icon": collection.icon,
                "created_at": collection.created_at.isoformat() if collection.created_at else None,
                "recipe_ids": [r.id for r in coll_recipes],
            }
        )

    # Meal plans and shopping lists belong to the household, not to one member
    plans = await db.execute(
        select(MealPlan)
        .where(MealPlan.household_id == household.id)
        .order_by(MealPlan.week_start_date)
        .options(selectinload(MealPlan.planned_meals))
    )
    export_data["meal_plans"] = [
        {
            "week_start_date": plan.week_start_date.isoformat(),
            "meals": [
                {
                    "recipe_id": meal.recipe_id,
                    "day_of_week": meal.day_of_week,
                    "meal_type": meal.meal_type,
                    "servings": meal.servings,
                    "notes": meal.notes,
                }
                for meal in sorted(plan.planned_meals, key=lambda m: (m.day_of_week, m.id))
            ],
        }
        for plan in plans.scalars()
    ]
    lists = await db.execute(
        select(ShoppingList)
        .where(ShoppingList.household_id == household.id)
        .order_by(ShoppingList.id)
        .options(selectinload(ShoppingList.items))
    )
    export_data["shopping_lists"] = [
        {
            "name": shopping_list.name,
            "description": shopping_list.description,
            "status": shopping_list.status,
            "items": [
                {
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "category": item.category,
                    "notes": item.notes,
                    "checked": item.checked,
                }
                for item in sorted(shopping_list.items, key=lambda i: (i.display_order, i.id))
            ],
        }
        for shopping_list in lists.scalars()
    ]

    return Response(
        content=json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="complete_backup_{datetime.now(UTC).strftime("%Y%m%d")}.json"'
        },
    )
