"""
Import API endpoints
Allows users to import recipes from JSON files in Schema.org format
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Literal
import json
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.recipe import Recipe
from app.models.collection import Collection, RecipeCollection
from app.utils.recipe_format import convert_from_schema_org

router = APIRouter()


@router.post("/recipes")
async def import_recipes(
    file: UploadFile = File(...),
    duplicate_handling: Literal["skip", "update", "create"] = Form("skip"),
    collection_id: int = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Import recipes from a JSON file in Schema.org Recipe format.

    Args:
        file: JSON file containing recipes (can be single recipe object or array of recipes)
        duplicate_handling: How to handle duplicate recipes (by name)
            - skip: Skip recipes with matching names
            - update: Update existing recipes with matching names
            - create: Always create new recipes (allow duplicates)
        collection_id: Optional collection ID to add imported recipes to
        current_user: Current authenticated user
        db: Database session

    Returns:
        Summary of import results
    """
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file")

    # Read and parse JSON
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    # Normalize to array of recipes
    if isinstance(data, dict):
        # Single recipe object
        recipes_data = [data]
    elif isinstance(data, list):
        # Array of recipes
        recipes_data = data
    else:
        raise HTTPException(status_code=400, detail="JSON must be a recipe object or array of recipes")

    # Validate collection if specified
    collection = None
    if collection_id:
        result = await db.execute(
            select(Collection)
            .where(Collection.id == collection_id)
            .where(Collection.user_id == current_user.id)
        )
        collection = result.scalar_one_or_none()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

    # Track import results
    results = {
        "total": len(recipes_data),
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
    }

    # Process each recipe
    for idx, recipe_data in enumerate(recipes_data):
        try:
            # Convert from Schema.org format to internal format
            recipe_dict = convert_from_schema_org(recipe_data)

            # Check for duplicate by name
            existing_recipe = None
            if duplicate_handling in ["skip", "update"]:
                result = await db.execute(
                    select(Recipe)
                    .where(Recipe.user_id == current_user.id)
                    .where(Recipe.name == recipe_dict["name"])
                    .where(Recipe.deleted_at.is_(None))
                )
                existing_recipe = result.scalar_one_or_none()

            if existing_recipe:
                if duplicate_handling == "skip":
                    results["skipped"] += 1
                    continue
                elif duplicate_handling == "update":
                    # Update existing recipe
                    existing_recipe.description = recipe_dict["description"]
                    existing_recipe.image_url = recipe_dict["image_url"]
                    existing_recipe.recipe_data = recipe_dict["recipe_data"]
                    existing_recipe.source_url = recipe_dict["source_url"]
                    existing_recipe.cuisine = recipe_dict["cuisine"]
                    existing_recipe.category = recipe_dict["category"]
                    existing_recipe.total_time_minutes = recipe_dict["total_time_minutes"]
                    existing_recipe.is_modified = True
                    existing_recipe.updated_at = datetime.utcnow()

                    results["updated"] += 1
                    recipe_to_add = existing_recipe
            else:
                # Create new recipe
                new_recipe = Recipe(
                    user_id=current_user.id,
                    name=recipe_dict["name"],
                    description=recipe_dict["description"],
                    image_url=recipe_dict["image_url"],
                    recipe_data=recipe_dict["recipe_data"],
                    source_url=recipe_dict["source_url"],
                    source_type=recipe_dict["source_type"],
                    cuisine=recipe_dict["cuisine"],
                    category=recipe_dict["category"],
                    total_time_minutes=recipe_dict["total_time_minutes"],
                    imported_at=datetime.utcnow(),
                )
                db.add(new_recipe)
                results["created"] += 1
                recipe_to_add = new_recipe

            # Add to collection if specified
            if collection and recipe_to_add:
                # Flush to get the recipe ID if it's new
                await db.flush()

                # Check if recipe is already in collection
                existing_link = await db.execute(
                    select(RecipeCollection)
                    .where(RecipeCollection.recipe_id == recipe_to_add.id)
                    .where(RecipeCollection.collection_id == collection.id)
                )
                if not existing_link.scalar_one_or_none():
                    db.add(RecipeCollection(
                        recipe_id=recipe_to_add.id,
                        collection_id=collection.id
                    ))

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "index": idx,
                "name": recipe_data.get("name", "Unknown"),
                "error": str(e)
            })

    # Commit all changes
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save recipes: {str(e)}")

    return {
        "success": True,
        "message": f"Imported {results['created']} new recipes, updated {results['updated']}, skipped {results['skipped']}, failed {results['failed']}",
        "details": results
    }


@router.post("/recipes/json")
async def import_recipes_json(
    recipes: List[Dict[str, Any]],
    duplicate_handling: Literal["skip", "update", "create"] = "skip",
    collection_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Import recipes from JSON data (for API/extension use).

    Args:
        recipes: Array of recipe objects in Schema.org format
        duplicate_handling: How to handle duplicate recipes
        collection_id: Optional collection ID to add recipes to
        current_user: Current authenticated user
        db: Database session

    Returns:
        Summary of import results
    """
    # Validate collection if specified
    collection = None
    if collection_id:
        result = await db.execute(
            select(Collection)
            .where(Collection.id == collection_id)
            .where(Collection.user_id == current_user.id)
        )
        collection = result.scalar_one_or_none()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

    # Track import results
    results = {
        "total": len(recipes),
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
    }

    # Process each recipe
    for idx, recipe_data in enumerate(recipes):
        try:
            # Convert from Schema.org format to internal format
            recipe_dict = convert_from_schema_org(recipe_data)

            # Check for duplicate by name
            existing_recipe = None
            if duplicate_handling in ["skip", "update"]:
                result = await db.execute(
                    select(Recipe)
                    .where(Recipe.user_id == current_user.id)
                    .where(Recipe.name == recipe_dict["name"])
                    .where(Recipe.deleted_at.is_(None))
                )
                existing_recipe = result.scalar_one_or_none()

            if existing_recipe:
                if duplicate_handling == "skip":
                    results["skipped"] += 1
                    continue
                elif duplicate_handling == "update":
                    # Update existing recipe
                    existing_recipe.description = recipe_dict["description"]
                    existing_recipe.image_url = recipe_dict["image_url"]
                    existing_recipe.recipe_data = recipe_dict["recipe_data"]
                    existing_recipe.source_url = recipe_dict["source_url"]
                    existing_recipe.cuisine = recipe_dict["cuisine"]
                    existing_recipe.category = recipe_dict["category"]
                    existing_recipe.total_time_minutes = recipe_dict["total_time_minutes"]
                    existing_recipe.is_modified = True
                    existing_recipe.updated_at = datetime.utcnow()

                    results["updated"] += 1
                    recipe_to_add = existing_recipe
            else:
                # Create new recipe
                new_recipe = Recipe(
                    user_id=current_user.id,
                    name=recipe_dict["name"],
                    description=recipe_dict["description"],
                    image_url=recipe_dict["image_url"],
                    recipe_data=recipe_dict["recipe_data"],
                    source_url=recipe_dict["source_url"],
                    source_type=recipe_dict["source_type"],
                    cuisine=recipe_dict["cuisine"],
                    category=recipe_dict["category"],
                    total_time_minutes=recipe_dict["total_time_minutes"],
                    imported_at=datetime.utcnow(),
                )
                db.add(new_recipe)
                results["created"] += 1
                recipe_to_add = new_recipe

            # Add to collection if specified
            if collection and recipe_to_add:
                # Flush to get the recipe ID if it's new
                await db.flush()

                # Check if recipe is already in collection
                existing_link = await db.execute(
                    select(RecipeCollection)
                    .where(RecipeCollection.recipe_id == recipe_to_add.id)
                    .where(RecipeCollection.collection_id == collection.id)
                )
                if not existing_link.scalar_one_or_none():
                    db.add(RecipeCollection(
                        recipe_id=recipe_to_add.id,
                        collection_id=collection.id
                    ))

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "index": idx,
                "name": recipe_data.get("name", "Unknown"),
                "error": str(e)
            })

    # Commit all changes
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save recipes: {str(e)}")

    return {
        "success": True,
        "message": f"Imported {results['created']} new recipes, updated {results['updated']}, skipped {results['skipped']}, failed {results['failed']}",
        "details": results
    }
