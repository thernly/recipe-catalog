"""
Recipe search and filtering operations.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.models.collection import RecipeCollection
from app.models.household import Household
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.recipe import RecipeSearchResult, RecipeSummary


router = APIRouter()


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
