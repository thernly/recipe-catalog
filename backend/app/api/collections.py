"""
Collection management API endpoints.
"""


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.models.collection import Collection, RecipeCollection
from app.models.household import Household
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.collection import (
    Collection as CollectionSchema,
)
from app.schemas.collection import (
    CollectionCreate,
    CollectionRecipeAdd,
    CollectionRecipeRemove,
    CollectionUpdate,
    CollectionWithCount,
)


router = APIRouter()


@router.post("/", response_model=CollectionSchema, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection_data: CollectionCreate,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new collection.

    Args:
        collection_data: Collection creation data
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        Collection: The created collection

    Raises:
        HTTPException: If collection name already exists for user
    """
    # Check if collection name already exists in the household
    result = await db.execute(
        select(Collection).where(
            Collection.household_id == household.id,
            Collection.name == collection_data.name,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collection with this name already exists",
        )

    # Create collection
    new_collection = Collection(
        user_id=current_user.id,
        household_id=household.id,
        name=collection_data.name,
        description=collection_data.description,
        icon=collection_data.icon,
        is_default=False,
    )

    db.add(new_collection)
    await db.commit()
    await db.refresh(new_collection)

    # Add creator display name
    collection_dict = {
        "id": new_collection.id,
        "user_id": new_collection.user_id,
        "name": new_collection.name,
        "description": new_collection.description,
        "icon": new_collection.icon,
        "is_default": new_collection.is_default,
        "created_at": new_collection.created_at,
        "updated_at": new_collection.updated_at,
        "creator_display_name": current_user.display_name,
    }

    return CollectionSchema(**collection_dict)


@router.get("/", response_model=list[CollectionWithCount])
async def list_collections(
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    List all collections for the current user's household.

    Args:
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        List[CollectionWithCount]: List of collections with recipe counts
    """
    # Get collections with recipe counts for the household
    stmt = (
        select(
            Collection,
            func.count(RecipeCollection.recipe_id).label("recipe_count"),
            User,
        )
        .outerjoin(RecipeCollection)
        .join(User, Collection.user_id == User.id)
        .where(Collection.household_id == household.id)
        .group_by(Collection.id, User.id)
        .order_by(Collection.is_default.desc(), Collection.created_at.asc())
    )

    result = await db.execute(stmt)
    collections_with_counts = result.all()

    return [
        CollectionWithCount(
            **collection.__dict__,
            recipe_count=count,
            creator_display_name=user.display_name,
        )
        for collection, count, user in collections_with_counts
    ]


@router.get("/{collection_id}", response_model=CollectionWithCount)
async def get_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single collection by ID.

    Args:
        collection_id: Collection ID
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        CollectionWithCount: The requested collection with recipe count

    Raises:
        HTTPException: If collection not found or unauthorized
    """
    # Get collection with recipe count and creator info
    stmt = (
        select(
            Collection,
            func.count(RecipeCollection.recipe_id).label("recipe_count"),
            User,
        )
        .outerjoin(RecipeCollection)
        .join(User, Collection.user_id == User.id)
        .where(Collection.id == collection_id, Collection.household_id == household.id)
        .group_by(Collection.id, User.id)
    )

    result = await db.execute(stmt)
    collection_with_count = result.first()

    if not collection_with_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    collection, count, user = collection_with_count

    return CollectionWithCount(
        **collection.__dict__,
        recipe_count=count,
        creator_display_name=user.display_name,
    )


@router.patch("/{collection_id}", response_model=CollectionSchema)
async def update_collection(
    collection_id: int,
    collection_update: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
            Collection.id == collection_id, Collection.user_id == current_user.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # Check if updating name and it already exists
    if collection_update.name is not None:
        result = await db.execute(
            select(Collection).where(
                Collection.user_id == current_user.id,
                Collection.name == collection_update.name,
                Collection.id != collection_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collection with this name already exists",
            )

    # Update fields
    update_data = collection_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(collection, field, value)

    await db.commit()
    await db.refresh(collection)

    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
            Collection.id == collection_id, Collection.user_id == current_user.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    if collection.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default collection",
        )

    await db.delete(collection)
    await db.commit()


@router.post("/{collection_id}/recipes")
async def add_recipes_to_collection(
    collection_id: int,
    recipe_data: CollectionRecipeAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add recipes to a collection.

    Args:
        collection_id: Collection ID
        recipe_data: Recipe IDs to add
        current_user: The authenticated user
        db: Database session

    Returns:
        dict: Results with successful, skipped, and failed recipe IDs

    Raises:
        HTTPException: If collection not found or unauthorized
    """
    # Verify collection exists and belongs to user
    result = await db.execute(
        select(Collection).where(
            Collection.id == collection_id, Collection.user_id == current_user.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # Track results
    added = []
    skipped = []
    not_found = []

    # Add recipes to collection
    for recipe_id in recipe_data.recipe_ids:
        # Verify recipe belongs to user
        result = await db.execute(
            select(Recipe).where(Recipe.id == recipe_id, Recipe.user_id == current_user.id)
        )
        recipe = result.scalar_one_or_none()

        if not recipe:
            not_found.append(recipe_id)
            continue

        # Check if already in collection
        result = await db.execute(
            select(RecipeCollection).where(
                RecipeCollection.recipe_id == recipe_id,
                RecipeCollection.collection_id == collection_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            skipped.append(recipe_id)
        else:
            recipe_collection = RecipeCollection(recipe_id=recipe_id, collection_id=collection_id)
            db.add(recipe_collection)
            added.append(recipe_id)

    await db.commit()

    return {
        "added": added,
        "skipped": skipped,
        "not_found": not_found,
        "message": f"Added {len(added)} recipes, skipped {len(skipped)} already in collection, {len(not_found)} not found",
    }


@router.delete("/{collection_id}/recipes", status_code=status.HTTP_204_NO_CONTENT)
async def remove_recipes_from_collection(
    collection_id: int,
    recipe_data: CollectionRecipeRemove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
            Collection.id == collection_id, Collection.user_id == current_user.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # Remove recipes from collection
    for recipe_id in recipe_data.recipe_ids:
        result = await db.execute(
            select(RecipeCollection).where(
                RecipeCollection.recipe_id == recipe_id,
                RecipeCollection.collection_id == collection_id,
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
    db: AsyncSession = Depends(get_db),
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
            Collection.id == collection_id, Collection.user_id == current_user.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # Get recipes in collection
    stmt = (
        select(Recipe)
        .join(RecipeCollection)
        .where(RecipeCollection.collection_id == collection_id, Recipe.deleted_at.is_(None))
        .order_by(RecipeCollection.added_at.desc())
    )

    result = await db.execute(stmt)
    recipes = result.scalars().all()

    return [RecipeSummary.model_validate(r) for r in recipes]


@router.get("/{collection_id}/export/pdf")
async def export_collection_pdf(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    household: Household = Depends(get_user_household),
    db: AsyncSession = Depends(get_db),
):
    """
    Export a collection as PDF.

    Args:
        collection_id: Collection ID
        current_user: The authenticated user
        household: The user's household
        db: Database session

    Returns:
        Response: The exported PDF file

    Raises:
        HTTPException: If collection not found or unauthorized
    """
    from fastapi import Response

    from app.utils.pdf_export import generate_collection_pdf

    # Verify collection exists and belongs to household
    result = await db.execute(
        select(Collection).where(
            Collection.id == collection_id, Collection.household_id == household.id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # Get recipes in collection
    stmt = (
        select(Recipe)
        .join(RecipeCollection)
        .where(RecipeCollection.collection_id == collection_id, Recipe.deleted_at.is_(None))
        .order_by(RecipeCollection.added_at.asc())
    )

    result = await db.execute(stmt)
    recipes = result.scalars().all()

    if not recipes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collection has no recipes to export",
        )

    # Check recipe count limit (max 50 recipes)
    if len(recipes) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Collection has {len(recipes)} recipes. Maximum 50 recipes allowed per PDF export.",
        )

    # Generate PDF
    pdf_bytes = generate_collection_pdf(collection.name, collection.description or "", recipes)

    # Generate safe filename
    safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in collection.name)
    safe_name = safe_name.replace(" ", "_").lower()[:50]

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.pdf"'},
    )
