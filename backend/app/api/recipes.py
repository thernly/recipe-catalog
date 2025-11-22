"""
Recipe CRUD API endpoints.
"""

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.core.security import sanitize_html
from app.models.collection import RecipeCollection
from app.models.household import Household
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.recipe import (
    Recipe as RecipeSchema,
)
from app.schemas.recipe import (
    RecipeCreate,
    RecipeSearchResult,
    RecipeSummary,
    RecipeUpdate,
)
from app.services.recipe_export import RecipeExporter


router = APIRouter()


def sanitize_recipe_data(data: dict) -> dict:
    """
    Recursively sanitize string values in recipe data dictionary.

    Args:
        data: Dictionary containing recipe data

    Returns:
        Dictionary with sanitized string values
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_html(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_recipe_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_recipe_data(item)
                if isinstance(item, dict)
                else sanitize_html(item)
                if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


@router.post("/", response_model=RecipeSchema, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new recipe.

    Args:
        recipe_data: Recipe creation data
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        Recipe: The created recipe
    """
    # Sanitize user input to prevent XSS attacks
    sanitized_name = sanitize_html(recipe_data.name) if recipe_data.name else None
    sanitized_description = (
        sanitize_html(recipe_data.description) if recipe_data.description else None
    )
    sanitized_recipe_data = sanitize_recipe_data(recipe_data.recipe_data)

    # Create recipe
    new_recipe = Recipe(
        user_id=current_user.id,
        household_id=household.id,
        name=sanitized_name,
        description=sanitized_description,
        image_url=recipe_data.image_url,
        recipe_data=sanitized_recipe_data,
        source_url=recipe_data.source_url,
        source_type=recipe_data.source_type,
        cuisine=recipe_data.cuisine,
        category=recipe_data.category,
        total_time_minutes=recipe_data.total_time_minutes,
        imported_at=datetime.now(UTC) if recipe_data.source_type == "imported" else None,
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

    # Add creator display name
    recipe_dict = {
        "id": new_recipe.id,
        "user_id": new_recipe.user_id,
        "name": new_recipe.name,
        "description": new_recipe.description,
        "image_url": new_recipe.image_url,
        "recipe_data": new_recipe.recipe_data,
        "source_url": new_recipe.source_url,
        "source_type": new_recipe.source_type,
        "is_modified": new_recipe.is_modified,
        "created_at": new_recipe.created_at,
        "updated_at": new_recipe.updated_at,
        "imported_at": new_recipe.imported_at,
        "deleted_at": new_recipe.deleted_at,
        "cuisine": new_recipe.cuisine,
        "category": new_recipe.category,
        "total_time_minutes": new_recipe.total_time_minutes,
        "creator_display_name": current_user.display_name,
    }

    return RecipeSchema(**recipe_dict)


@router.get("/search", response_model=RecipeSearchResult)
async def search_recipes(
    query: str | None = Query(None),
    cuisine: list[str] | None = Query(None),
    category: list[str] | None = Query(None),
    source_type: list[str] | None = Query(None),
    collection_ids: list[int] | None = Query(None),
    max_time_minutes: int | None = Query(None),
    min_time_minutes: int | None = Query(None),
    sort_by: str = Query("recently_added"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
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
        household: The user's household
        db: Database session

    Returns:
        RecipeSearchResult: Paginated search results
    """
    # Base query for active recipes in the user's household
    stmt = select(Recipe).where(Recipe.household_id == household.id, Recipe.deleted_at.is_(None))

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
        stmt = stmt.join(RecipeCollection).where(RecipeCollection.collection_id.in_(collection_ids))

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
        recipes=[RecipeSummary.model_validate(r) for r in recipes],
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
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single recipe by ID.

    Args:
        recipe_id: Recipe ID
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        Recipe: The requested recipe

    Raises:
        HTTPException: If recipe not found or unauthorized
    """
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.household_id == household.id)
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    # Get creator display name
    user_result = await db.execute(select(User).where(User.id == recipe.user_id))
    creator = user_result.scalar_one_or_none()

    # Create response with creator info
    recipe_dict = {
        "id": recipe.id,
        "user_id": recipe.user_id,
        "name": recipe.name,
        "description": recipe.description,
        "image_url": recipe.image_url,
        "recipe_data": recipe.recipe_data,
        "source_url": recipe.source_url,
        "source_type": recipe.source_type,
        "is_modified": recipe.is_modified,
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at,
        "imported_at": recipe.imported_at,
        "deleted_at": recipe.deleted_at,
        "cuisine": recipe.cuisine,
        "category": recipe.category,
        "total_time_minutes": recipe.total_time_minutes,
        "creator_display_name": creator.display_name if creator else None,
    }

    # TODO: Track recipe view for "recently viewed" feature

    return RecipeSchema(**recipe_dict)


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    # Update fields with sanitization
    update_data = recipe_update.model_dump(exclude_unset=True, exclude={"collection_ids"})

    # Sanitize text fields
    if "name" in update_data and update_data["name"]:
        update_data["name"] = sanitize_html(update_data["name"])
    if "description" in update_data and update_data["description"]:
        update_data["description"] = sanitize_html(update_data["description"])
    if "recipe_data" in update_data and update_data["recipe_data"]:
        update_data["recipe_data"] = sanitize_recipe_data(update_data["recipe_data"])

    for field, value in update_data.items():
        setattr(recipe, field, value)

    # Mark as modified if it was imported
    if recipe.source_type == "imported":
        recipe.is_modified = True

    # Update collections if specified
    if recipe_update.collection_ids is not None:
        # Remove existing collections
        await db.execute(select(RecipeCollection).where(RecipeCollection.recipe_id == recipe_id))

        # Add new collections
        for collection_id in recipe_update.collection_ids:
            recipe_collection = RecipeCollection(recipe_id=recipe.id, collection_id=collection_id)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    if permanent:
        # Permanent delete
        await db.delete(recipe)
    else:
        # Soft delete
        recipe.deleted_at = datetime.now(UTC)

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    if recipe.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipe is not deleted")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

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
    format: Literal["json", "markdown", "text", "pdf"] = "json",
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Export a single recipe in the specified format.

    Args:
        recipe_id: Recipe ID to export
        format: Export format (json, markdown, text, or pdf)
        current_user: The authenticated user
        household: The user's household
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
            Recipe.household_id == household.id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    # Generate safe filename from recipe name
    safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in recipe.name)
    safe_name = safe_name.replace(" ", "_").lower()[:50]  # Limit length

    # Use RecipeExporter service
    exporter = RecipeExporter()

    if format == "pdf":
        pdf_bytes = exporter.export_pdf(recipe)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.pdf"'},
        )

    elif format == "json":
        content = exporter.export_json(recipe)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.json"'},
        )

    elif format == "markdown":
        content = exporter.export_markdown(recipe)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.md"'},
        )

    elif format == "text":
        content = exporter.export_text(recipe)
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.txt"'},
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid export format")


@router.get("/trash/list", response_model=list[RecipeSummary])
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

    return [RecipeSummary.model_validate(r) for r in recipes]
