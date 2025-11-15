"""
Export API endpoints
Allows users to export their recipe data in various formats
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Literal
import json
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.recipe import Recipe
from app.models.collection import Collection, RecipeCollection
from app.utils.recipe_format import convert_to_schema_org

router = APIRouter()


@router.get("/recipes")
async def export_recipes(
    format: Literal["json", "markdown", "text"] = "json",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export all user recipes in the specified format.

    Formats:
    - json: Complete recipe data in JSON format
    - markdown: Human-readable markdown format
    - text: Plain text format
    """
    # Fetch all user recipes (not deleted)
    result = await db.execute(
        select(Recipe)
        .where(Recipe.user_id == current_user.id)
        .where(Recipe.deleted_at.is_(None))
        .order_by(Recipe.created_at.desc())
    )
    recipes = result.scalars().all()

    if format == "json":
        # Export as JSON in Schema.org Recipe format
        recipes_schema_org = [convert_to_schema_org(recipe) for recipe in recipes]

        # Return as downloadable JSON file
        # Export as array of recipes (not wrapped in object)
        return Response(
            content=json.dumps(recipes_schema_org, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="recipes_export_{datetime.utcnow().strftime("%Y%m%d")}.json"'
            },
        )

    elif format == "markdown":
        # Export as Markdown
        lines = [
            f"# Recipe Export - {current_user.display_name}",
            f"\nExported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"\nTotal Recipes: {len(recipes)}",
            "\n---\n",
        ]

        for recipe in recipes:
            lines.append(f"\n## {recipe.name}\n")

            if recipe.description:
                lines.append(f"{recipe.description}\n")

            lines.append(f"\n**Cuisine:** {recipe.cuisine or 'N/A'}")
            lines.append(f"**Category:** {recipe.category or 'N/A'}")

            if recipe.total_time_minutes:
                lines.append(f"**Total Time:** {recipe.total_time_minutes} minutes")

            if recipe.source_url:
                lines.append(f"**Source:** {recipe.source_url}")

            # Add recipe data if available
            if recipe.recipe_data:
                recipe_data = recipe.recipe_data

                if isinstance(recipe_data, dict):
                    if recipe_data.get("ingredients"):
                        lines.append("\n### Ingredients\n")
                        for ingredient in recipe_data["ingredients"]:
                            if isinstance(ingredient, str):
                                lines.append(f"- {ingredient}")
                            elif isinstance(ingredient, dict):
                                lines.append(f"- {ingredient.get('name', '')} {ingredient.get('amount', '')}")

                    if recipe_data.get("instructions"):
                        lines.append("\n### Instructions\n")
                        instructions = recipe_data["instructions"]
                        if isinstance(instructions, list):
                            for i, step in enumerate(instructions, 1):
                                lines.append(f"{i}. {step}")
                        elif isinstance(instructions, str):
                            lines.append(instructions)

            lines.append("\n---\n")

        content = "\n".join(lines)

        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="recipes_export_{datetime.utcnow().strftime("%Y%m%d")}.md"'
            },
        )

    elif format == "text":
        # Export as plain text
        lines = [
            f"RECIPE EXPORT - {current_user.display_name}",
            f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Total Recipes: {len(recipes)}",
            "\n" + "="*80 + "\n",
        ]

        for recipe in recipes:
            lines.append(f"\n{recipe.name.upper()}")
            lines.append("-" * len(recipe.name))

            if recipe.description:
                lines.append(f"\n{recipe.description}\n")

            lines.append(f"Cuisine: {recipe.cuisine or 'N/A'}")
            lines.append(f"Category: {recipe.category or 'N/A'}")

            if recipe.total_time_minutes:
                lines.append(f"Total Time: {recipe.total_time_minutes} minutes")

            if recipe.source_url:
                lines.append(f"Source: {recipe.source_url}")

            # Add recipe data if available
            if recipe.recipe_data:
                recipe_data = recipe.recipe_data

                if isinstance(recipe_data, dict):
                    if recipe_data.get("ingredients"):
                        lines.append("\nINGREDIENTS:")
                        for ingredient in recipe_data["ingredients"]:
                            if isinstance(ingredient, str):
                                lines.append(f"  - {ingredient}")
                            elif isinstance(ingredient, dict):
                                lines.append(f"  - {ingredient.get('name', '')} {ingredient.get('amount', '')}")

                    if recipe_data.get("instructions"):
                        lines.append("\nINSTRUCTIONS:")
                        instructions = recipe_data["instructions"]
                        if isinstance(instructions, list):
                            for i, step in enumerate(instructions, 1):
                                lines.append(f"  {i}. {step}")
                        elif isinstance(instructions, str):
                            lines.append(f"  {instructions}")

            lines.append("\n" + "="*80 + "\n")

        content = "\n".join(lines)

        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="recipes_export_{datetime.utcnow().strftime("%Y%m%d")}.txt"'
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
            "export_date": datetime.utcnow().isoformat(),
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

            export_data["collections"].append({
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "created_at": collection.created_at.isoformat() if collection.created_at else None,
                "recipe_count": len(recipes),
                "recipes": [
                    {
                        "id": recipe.id,
                        "name": recipe.name,
                        "description": recipe.description,
                    }
                    for recipe in recipes
                ],
            })

        return Response(
            content=json.dumps(export_data, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="collections_export_{datetime.utcnow().strftime("%Y%m%d")}.json"'
            },
        )

    elif format == "markdown":
        # Export as Markdown
        lines = [
            f"# Collections Export - {current_user.display_name}",
            f"\nExported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
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
                "Content-Disposition": f'attachment; filename="collections_export_{datetime.utcnow().strftime("%Y%m%d")}.md"'
            },
        )

    else:
        raise HTTPException(status_code=400, detail="Format not supported for collections")


@router.get("/all")
async def export_all_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export all user data (recipes, collections, preferences) as JSON.
    """
    # Fetch recipes
    recipe_result = await db.execute(
        select(Recipe)
        .where(Recipe.user_id == current_user.id)
        .where(Recipe.deleted_at.is_(None))
        .order_by(Recipe.created_at.desc())
    )
    recipes = recipe_result.scalars().all()

    # Fetch collections
    collection_result = await db.execute(
        select(Collection)
        .where(Collection.user_id == current_user.id)
        .order_by(Collection.created_at.desc())
    )
    collections = collection_result.scalars().all()

    # Build complete export
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "export_type": "complete_backup",
        "user": {
            "email": current_user.email,
            "display_name": current_user.display_name,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "preferences": {
            "theme": current_user.preferences.theme if current_user.preferences else "classic",
            "default_view": current_user.preferences.default_view if current_user.preferences else "grid",
            "default_sort": current_user.preferences.default_sort if current_user.preferences else "recently_added",
        } if current_user.preferences else None,
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

        export_data["collections"].append({
            "id": collection.id,
            "name": collection.name,
            "description": collection.description,
            "created_at": collection.created_at.isoformat() if collection.created_at else None,
            "recipe_ids": [r.id for r in coll_recipes],
        })

    return Response(
        content=json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="complete_backup_{datetime.utcnow().strftime("%Y%m%d")}.json"'
        },
    )
