"""
Recipe CRUD API endpoints.
"""

from datetime import datetime, timezone
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
import json

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.recipe import Recipe
from app.models.collection import RecipeCollection
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    Recipe as RecipeSchema,
    RecipeSummary,
    RecipeSearchResult,
)
from app.utils.recipe_format import convert_to_schema_org

router = APIRouter()


@router.post("/", response_model=RecipeSchema, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new recipe.

    Args:
        recipe_data: Recipe creation data
        current_user: The authenticated user
        db: Database session

    Returns:
        Recipe: The created recipe
    """
    # Create recipe
    new_recipe = Recipe(
        user_id=current_user.id,
        name=recipe_data.name,
        description=recipe_data.description,
        image_url=recipe_data.image_url,
        recipe_data=recipe_data.recipe_data,
        source_url=recipe_data.source_url,
        source_type=recipe_data.source_type,
        cuisine=recipe_data.cuisine,
        category=recipe_data.category,
        total_time_minutes=recipe_data.total_time_minutes,
        imported_at=datetime.now(timezone.utc)
        if recipe_data.source_type == "imported"
        else None,
    )

    db.add(new_recipe)
    await db.flush()

    # Add to collections if specified
    if recipe_data.collection_ids:
        for collection_id in recipe_data.collection_ids:
            recipe_collection = RecipeCollection(
                recipe_id=new_recipe.id, collection_id=collection_id
            )
            db.add(recipe_collection)

    await db.commit()
    await db.refresh(new_recipe)

    return new_recipe


@router.get("/search", response_model=RecipeSearchResult)
async def search_recipes(
    query: Optional[str] = Query(None),
    cuisine: Optional[List[str]] = Query(None),
    category: Optional[List[str]] = Query(None),
    source_type: Optional[List[str]] = Query(None),
    collection_ids: Optional[List[int]] = Query(None),
    max_time_minutes: Optional[int] = Query(None),
    min_time_minutes: Optional[int] = Query(None),
    sort_by: str = Query("recently_added"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search and filter recipes.

    Args:
        query: Search query string
        cuisine: List of cuisines to filter by
        category: List of categories to filter by
        source_type: List of source types to filter by
        collection_ids: List of collection IDs to filter by
        max_time_minutes: Maximum cooking time
        min_time_minutes: Minimum cooking time
        sort_by: Sort order
        page: Page number
        per_page: Results per page
        current_user: The authenticated user
        db: Database session

    Returns:
        RecipeSearchResult: Paginated search results
    """
    # Base query for active recipes
    stmt = select(Recipe).where(
        Recipe.user_id == current_user.id, Recipe.deleted_at.is_(None)
    )

    # Apply text search
    if query:
        search_term = f"%{query}%"
        stmt = stmt.where(
            or_(
                Recipe.name.ilike(search_term),
                Recipe.description.ilike(search_term),
                Recipe.cuisine.ilike(search_term),
                Recipe.category.ilike(search_term),
            )
        )

    # Apply filters
    if cuisine:
        stmt = stmt.where(Recipe.cuisine.in_(cuisine))

    if category:
        stmt = stmt.where(Recipe.category.in_(category))

    if source_type:
        stmt = stmt.where(Recipe.source_type.in_(source_type))

    if max_time_minutes is not None:
        stmt = stmt.where(Recipe.total_time_minutes <= max_time_minutes)

    if min_time_minutes is not None:
        stmt = stmt.where(Recipe.total_time_minutes >= min_time_minutes)

    if collection_ids:
        # Join with recipe_collections to filter by collections
        stmt = stmt.join(RecipeCollection).where(
            RecipeCollection.collection_id.in_(collection_ids)
        )

    # Apply sorting
    if sort_by == "alphabetical":
        stmt = stmt.order_by(Recipe.name.asc())
    elif sort_by == "time_asc":
        stmt = stmt.order_by(Recipe.total_time_minutes.asc())
    elif sort_by == "time_desc":
        stmt = stmt.order_by(Recipe.total_time_minutes.desc())
    else:  # recently_added (default)
        stmt = stmt.order_by(Recipe.created_at.desc())

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    result = await db.execute(count_stmt)
    total = result.scalar()

    # Apply pagination
    offset = (page - 1) * per_page
    stmt = stmt.limit(per_page).offset(offset)

    # Execute query
    result = await db.execute(stmt)
    recipes = result.scalars().all()

    # Calculate pagination info
    total_pages = (total + per_page - 1) // per_page

    return RecipeSearchResult(
        recipes=[RecipeSummary.from_orm(r) for r in recipes],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get("/{recipe_id}", response_model=RecipeSchema)
async def get_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single recipe by ID.

    Args:
        recipe_id: Recipe ID
        current_user: The authenticated user
        db: Database session

    Returns:
        Recipe: The requested recipe

    Raises:
        HTTPException: If recipe not found or unauthorized
    """
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.user_id == current_user.id)
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    # TODO: Track recipe view for "recently viewed" feature

    return recipe


@router.patch("/{recipe_id}", response_model=RecipeSchema)
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a recipe.

    Args:
        recipe_id: Recipe ID
        recipe_update: Recipe update data
        current_user: The authenticated user
        db: Database session

    Returns:
        Recipe: The updated recipe

    Raises:
        HTTPException: If recipe not found or unauthorized
    """
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.user_id == current_user.id)
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    # Update fields
    update_data = recipe_update.model_dump(exclude_unset=True, exclude={"collection_ids"})
    for field, value in update_data.items():
        setattr(recipe, field, value)

    # Mark as modified if it was imported
    if recipe.source_type == "imported":
        recipe.is_modified = True

    # Update collections if specified
    if recipe_update.collection_ids is not None:
        # Remove existing collections
        await db.execute(
            select(RecipeCollection).where(RecipeCollection.recipe_id == recipe_id)
        )

        # Add new collections
        for collection_id in recipe_update.collection_ids:
            recipe_collection = RecipeCollection(
                recipe_id=recipe.id, collection_id=collection_id
            )
            db.add(recipe_collection)

    await db.commit()
    await db.refresh(recipe)

    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    permanent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a recipe (soft delete by default).

    Args:
        recipe_id: Recipe ID
        permanent: If True, permanently delete; otherwise soft delete
        current_user: The authenticated user
        db: Database session

    Raises:
        HTTPException: If recipe not found or unauthorized
    """
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.user_id == current_user.id)
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    if permanent:
        # Permanent delete
        await db.delete(recipe)
    else:
        # Soft delete
        recipe.deleted_at = datetime.now(timezone.utc)

    await db.commit()


@router.post("/{recipe_id}/restore", response_model=RecipeSchema)
async def restore_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a soft-deleted recipe.

    Args:
        recipe_id: Recipe ID
        current_user: The authenticated user
        db: Database session

    Returns:
        Recipe: The restored recipe

    Raises:
        HTTPException: If recipe not found or not deleted
    """
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.user_id == current_user.id)
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    if recipe.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Recipe is not deleted"
        )

    recipe.deleted_at = None
    await db.commit()
    await db.refresh(recipe)

    return recipe


@router.post(
    "/{recipe_id}/duplicate",
    response_model=RecipeSchema,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Duplicate a recipe.

    Args:
        recipe_id: Recipe ID to duplicate
        current_user: The authenticated user
        db: Database session

    Returns:
        Recipe: The duplicated recipe

    Raises:
        HTTPException: If recipe not found
    """
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.user_id == current_user.id,
            Recipe.deleted_at.is_(None),
        )
    )
    original_recipe = result.scalar_one_or_none()

    if not original_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    # Create duplicate
    duplicate = Recipe(
        user_id=current_user.id,
        name=f"{original_recipe.name} (Copy)",
        description=original_recipe.description,
        image_url=original_recipe.image_url,
        recipe_data=original_recipe.recipe_data,
        source_url=original_recipe.source_url,
        source_type="manual",  # Duplicates are always manual
        cuisine=original_recipe.cuisine,
        category=original_recipe.category,
        total_time_minutes=original_recipe.total_time_minutes,
    )

    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)

    return duplicate


@router.get("/{recipe_id}/export")
async def export_recipe(
    recipe_id: int,
    format: Literal["json", "markdown", "text"] = "json",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export a single recipe in the specified format.

    Args:
        recipe_id: Recipe ID to export
        format: Export format (json, markdown, or text)
        current_user: The authenticated user
        db: Database session

    Returns:
        Response: The exported recipe file

    Raises:
        HTTPException: If recipe not found or user doesn't have access
    """
    # Fetch the recipe
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.user_id == current_user.id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    # Generate safe filename from recipe name
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in recipe.name)
    safe_name = safe_name.replace(' ', '_').lower()[:50]  # Limit length

    if format == "json":
        # Export as JSON in Schema.org Recipe format
        schema_recipe = convert_to_schema_org(recipe)

        return Response(
            content=json.dumps(schema_recipe, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}.json"'
            },
        )

    elif format == "markdown":
        # Export as Markdown
        schema_recipe = convert_to_schema_org(recipe)

        lines = [f"# {schema_recipe['name']}\n"]

        if schema_recipe.get('description'):
            lines.append(f"{schema_recipe['description']}\n")

        # Metadata section
        metadata_items = []
        if schema_recipe.get('recipeYield'):
            metadata_items.append(f"**Yield:** {schema_recipe['recipeYield']}")
        if schema_recipe.get('prepTime'):
            metadata_items.append(f"**Prep Time:** {schema_recipe['prepTime']}")
        if schema_recipe.get('cookTime'):
            metadata_items.append(f"**Cook Time:** {schema_recipe['cookTime']}")
        if schema_recipe.get('totalTime'):
            metadata_items.append(f"**Total Time:** {schema_recipe['totalTime']}")
        if schema_recipe.get('recipeCategory'):
            categories = schema_recipe['recipeCategory']
            category_str = ', '.join(categories) if isinstance(categories, list) else str(categories)
            metadata_items.append(f"**Category:** {category_str}")
        if schema_recipe.get('recipeCuisine'):
            cuisines = schema_recipe['recipeCuisine']
            cuisine_str = ', '.join(cuisines) if isinstance(cuisines, list) else str(cuisines)
            metadata_items.append(f"**Cuisine:** {cuisine_str}")
        if schema_recipe.get('keywords'):
            metadata_items.append(f"**Keywords:** {schema_recipe['keywords']}")
        if schema_recipe.get('url'):
            metadata_items.append(f"**Source:** {schema_recipe['url']}")

        if metadata_items:
            lines.append("")
            lines.extend(metadata_items)

        # Ingredients
        if schema_recipe.get('recipeIngredient'):
            lines.append("\n## Ingredients")
            for ingredient in schema_recipe['recipeIngredient']:
                lines.append(f"- {ingredient}")

        # Equipment
        if schema_recipe.get('equipment'):
            lines.append("\n## Equipment")
            equipment = schema_recipe['equipment']
            if isinstance(equipment, list):
                for item in equipment:
                    lines.append(f"- {item}")
            elif isinstance(equipment, str):
                lines.append(f"- {equipment}")

        # Instructions
        if schema_recipe.get('recipeInstructions'):
            lines.append("\n## Instructions")
            instructions = schema_recipe['recipeInstructions']
            if isinstance(instructions, list):
                for i, step in enumerate(instructions, 1):
                    if isinstance(step, dict):
                        step_text = step.get('text', str(step))
                    else:
                        step_text = str(step)
                    lines.append(f"{i}. {step_text}")
            elif isinstance(instructions, str):
                lines.append(instructions)

        # Notes
        if schema_recipe.get('notes'):
            lines.append("\n## Notes\n")
            lines.append(schema_recipe['notes'])

        # Nutrition
        if schema_recipe.get('nutrition'):
            nutrition = schema_recipe['nutrition']
            if isinstance(nutrition, dict) and nutrition:
                lines.append("\n## Nutrition Information\n")
                for key, value in nutrition.items():
                    if value:
                        label = ''.join([' ' + c if c.isupper() else c for c in key]).strip().title()
                        lines.append(f"- **{label}:** {value}")

        content = "\n".join(lines)

        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}.md"'
            },
        )

    elif format == "text":
        # Export as plain text
        schema_recipe = convert_to_schema_org(recipe)

        lines = [
            f"{schema_recipe['name'].upper()}",
            "=" * len(schema_recipe['name']),
        ]

        if schema_recipe.get('description'):
            lines.append(f"\n{schema_recipe['description']}\n")

        # Metadata
        if schema_recipe.get('recipeYield'):
            lines.append(f"Yield: {schema_recipe['recipeYield']}")
        if schema_recipe.get('prepTime'):
            lines.append(f"Prep Time: {schema_recipe['prepTime']}")
        if schema_recipe.get('cookTime'):
            lines.append(f"Cook Time: {schema_recipe['cookTime']}")
        if schema_recipe.get('totalTime'):
            lines.append(f"Total Time: {schema_recipe['totalTime']}")
        if schema_recipe.get('recipeCategory'):
            categories = schema_recipe['recipeCategory']
            category_str = ', '.join(categories) if isinstance(categories, list) else str(categories)
            lines.append(f"Category: {category_str}")
        if schema_recipe.get('recipeCuisine'):
            cuisines = schema_recipe['recipeCuisine']
            cuisine_str = ', '.join(cuisines) if isinstance(cuisines, list) else str(cuisines)
            lines.append(f"Cuisine: {cuisine_str}")
        if schema_recipe.get('keywords'):
            lines.append(f"Keywords: {schema_recipe['keywords']}")
        if schema_recipe.get('url'):
            lines.append(f"Source: {schema_recipe['url']}")

        # Ingredients
        if schema_recipe.get('recipeIngredient'):
            lines.append("\nINGREDIENTS:")
            for ingredient in schema_recipe['recipeIngredient']:
                lines.append(f"  - {ingredient}")

        # Equipment
        if schema_recipe.get('equipment'):
            lines.append("\nEQUIPMENT:")
            equipment = schema_recipe['equipment']
            if isinstance(equipment, list):
                for item in equipment:
                    lines.append(f"  - {item}")
            elif isinstance(equipment, str):
                lines.append(f"  - {equipment}")

        # Instructions
        if schema_recipe.get('recipeInstructions'):
            lines.append("\nINSTRUCTIONS:")
            instructions = schema_recipe['recipeInstructions']
            if isinstance(instructions, list):
                for i, step in enumerate(instructions, 1):
                    if isinstance(step, dict):
                        step_text = step.get('text', str(step))
                    else:
                        step_text = str(step)
                    lines.append(f"  {i}. {step_text}")
            elif isinstance(instructions, str):
                lines.append(f"  {instructions}")

        # Notes
        if schema_recipe.get('notes'):
            lines.append("\nNOTES:")
            lines.append(f"  {schema_recipe['notes']}")

        # Nutrition
        if schema_recipe.get('nutrition'):
            nutrition = schema_recipe['nutrition']
            if isinstance(nutrition, dict) and nutrition:
                lines.append("\nNUTRITION INFORMATION:")
                for key, value in nutrition.items():
                    if value:
                        label = ''.join([' ' + c if c.isupper() else c for c in key]).strip().title()
                        lines.append(f"  {label}: {value}")

        content = "\n".join(lines)

        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}.txt"'
            },
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid export format")


@router.get("/trash/list", response_model=List[RecipeSummary])
async def list_trashed_recipes(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    List all soft-deleted recipes.

    Args:
        current_user: The authenticated user
        db: Database session

    Returns:
        List[RecipeSummary]: List of trashed recipes
    """
    result = await db.execute(
        select(Recipe)
        .where(Recipe.user_id == current_user.id, Recipe.deleted_at.isnot(None))
        .order_by(Recipe.deleted_at.desc())
    )
    recipes = result.scalars().all()

    return [RecipeSummary.from_orm(r) for r in recipes]
