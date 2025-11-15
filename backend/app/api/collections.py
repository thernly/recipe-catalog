"""
Collection management API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.collection import Collection, RecipeCollection
from app.models.recipe import Recipe
from app.schemas.collection import (
    CollectionCreate,
    CollectionUpdate,
    Collection as CollectionSchema,
    CollectionWithCount,
    CollectionRecipeAdd,
    CollectionRecipeRemove,
)

router = APIRouter()


@router.post("/", response_model=CollectionSchema, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection_data: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new collection.

    Args:
        collection_data: Collection creation data
        current_user: The authenticated user
        db: Database session

    Returns:
        Collection: The created collection

    Raises:
        HTTPException: If collection name already exists for user
    """
    # Check if collection name already exists
    result = await db.execute(
        select(Collection).where(
            Collection.user_id == current_user.id,
            Collection.name == collection_data.name
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collection with this name already exists"
        )

    # Create collection
    new_collection = Collection(
        user_id=current_user.id,
        name=collection_data.name,
        description=collection_data.description,
        icon=collection_data.icon,
        is_default=False,
    )

    db.add(new_collection)
    await db.commit()
    await db.refresh(new_collection)

    return new_collection


@router.get("/", response_model=List[CollectionWithCount])
async def list_collections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all collections for the current user.

    Args:
        current_user: The authenticated user
        db: Database session

    Returns:
        List[CollectionWithCount]: List of collections with recipe counts
    """
    # Get collections with recipe counts
    stmt = (
        select(
            Collection,
            func.count(RecipeCollection.recipe_id).label("recipe_count")
        )
        .outerjoin(RecipeCollection)
        .where(Collection.user_id == current_user.id)
        .group_by(Collection.id)
        .order_by(Collection.is_default.desc(), Collection.created_at.asc())
    )

    result = await db.execute(stmt)
    collections_with_counts = result.all()

    return [
        CollectionWithCount(
            **collection.__dict__,
            recipe_count=count
        )
        for collection, count in collections_with_counts
    ]


@router.get("/{collection_id}", response_model=CollectionWithCount)
async def get_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single collection by ID.

    Args:
        collection_id: Collection ID
        current_user: The authenticated user
        db: Database session

    Returns:
        CollectionWithCount: The requested collection with recipe count

    Raises:
        HTTPException: If collection not found or unauthorized
    """
    # Get collection with recipe count
    stmt = (
        select(
            Collection,
            func.count(RecipeCollection.recipe_id).label("recipe_count")
        )
        .outerjoin(RecipeCollection)
        .where(
            Collection.id == collection_id,
            Collection.user_id == current_user.id
        )
        .group_by(Collection.id)
    )

    result = await db.execute(stmt)
    collection_with_count = result.first()

    if not collection_with_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    collection, count = collection_with_count

    return CollectionWithCount(
        **collection.__dict__,
        recipe_count=count
    )


@router.patch("/{collection_id}", response_model=CollectionSchema)
async def update_collection(
    collection_id: int,
    collection_update: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a collection.

    Args:
        collection_id: Collection ID
        collection_update: Collection update data
        current_user: The authenticated user
        db: Database session

    Returns:
        Collection: The updated collection

    Raises:
        HTTPException: If collection not found, unauthorized, or name already exists
    """
    result = await db.execute(
        select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == current_user.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    # Check if updating name and it already exists
    if collection_update.name is not None:
        result = await db.execute(
            select(Collection).where(
                Collection.user_id == current_user.id,
                Collection.name == collection_update.name,
                Collection.id != collection_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collection with this name already exists"
            )

    # Update fields
    update_data = collection_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(collection, field, value)

    await db.commit()
    await db.refresh(collection)

    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a collection (recipes are not deleted).

    Args:
        collection_id: Collection ID
        current_user: The authenticated user
        db: Database session

    Raises:
        HTTPException: If collection not found, unauthorized, or is default
    """
    result = await db.execute(
        select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == current_user.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    if collection.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default collection"
        )

    await db.delete(collection)
    await db.commit()


@router.post("/{collection_id}/recipes", status_code=status.HTTP_204_NO_CONTENT)
async def add_recipes_to_collection(
    collection_id: int,
    recipe_data: CollectionRecipeAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add recipes to a collection.

    Args:
        collection_id: Collection ID
        recipe_data: Recipe IDs to add
        current_user: The authenticated user
        db: Database session

    Raises:
        HTTPException: If collection not found or unauthorized
    """
    # Verify collection exists and belongs to user
    result = await db.execute(
        select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == current_user.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    # Add recipes to collection (ignore duplicates)
    for recipe_id in recipe_data.recipe_ids:
        # Verify recipe belongs to user
        result = await db.execute(
            select(Recipe).where(
                Recipe.id == recipe_id,
                Recipe.user_id == current_user.id
            )
        )
        recipe = result.scalar_one_or_none()

        if not recipe:
            continue  # Skip invalid recipe IDs

        # Check if already in collection
        result = await db.execute(
            select(RecipeCollection).where(
                RecipeCollection.recipe_id == recipe_id,
                RecipeCollection.collection_id == collection_id
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            recipe_collection = RecipeCollection(
                recipe_id=recipe_id,
                collection_id=collection_id
            )
            db.add(recipe_collection)

    await db.commit()


@router.delete("/{collection_id}/recipes", status_code=status.HTTP_204_NO_CONTENT)
async def remove_recipes_from_collection(
    collection_id: int,
    recipe_data: CollectionRecipeRemove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove recipes from a collection.

    Args:
        collection_id: Collection ID
        recipe_data: Recipe IDs to remove
        current_user: The authenticated user
        db: Database session

    Raises:
        HTTPException: If collection not found or unauthorized
    """
    # Verify collection exists and belongs to user
    result = await db.execute(
        select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == current_user.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    # Remove recipes from collection
    for recipe_id in recipe_data.recipe_ids:
        result = await db.execute(
            select(RecipeCollection).where(
                RecipeCollection.recipe_id == recipe_id,
                RecipeCollection.collection_id == collection_id
            )
        )
        recipe_collection = result.scalar_one_or_none()

        if recipe_collection:
            await db.delete(recipe_collection)

    await db.commit()


@router.get("/{collection_id}/recipes")
async def get_collection_recipes(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all recipes in a collection.

    Args:
        collection_id: Collection ID
        current_user: The authenticated user
        db: Database session

    Returns:
        List[RecipeSummary]: List of recipes in the collection

    Raises:
        HTTPException: If collection not found or unauthorized
    """
    from app.schemas.recipe import RecipeSummary

    # Verify collection exists
    result = await db.execute(
        select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == current_user.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    # Get recipes in collection
    stmt = (
        select(Recipe)
        .join(RecipeCollection)
        .where(
            RecipeCollection.collection_id == collection_id,
            Recipe.deleted_at.is_(None)
        )
        .order_by(RecipeCollection.added_at.desc())
    )

    result = await db.execute(stmt)
    recipes = result.scalars().all()

    return [RecipeSummary.from_orm(r) for r in recipes]
