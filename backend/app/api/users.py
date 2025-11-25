"""
User profile and preferences API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import get_password_hash, verify_password
from app.models.collection import Collection
from app.models.recipe import Recipe
from app.models.user import User
from app.models.user import UserPreferences as UserPrefsModel
from app.schemas.user import (
    PasswordChange,
    UserPreferences,
    UserPreferencesUpdate,
    UserUpdate,
)
from app.schemas.user import (
    User as UserSchema,
)


router = APIRouter()


@router.get("/me", response_model=UserSchema)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.

    Args:
        current_user: The authenticated user

    Returns:
        User: Current user profile
    """
    return current_user


@router.patch("/me", response_model=UserSchema)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user profile.

    Args:
        user_update: Profile update data
        current_user: The authenticated user
        db: Database session

    Returns:
        User: Updated user profile
    """
    if user_update.display_name is not None:
        current_user.display_name = user_update.display_name

    if user_update.email is not None:
        # Check if new email is already in use
        result = await db.execute(
            select(User).where(User.email == user_update.email.lower(), User.id != current_user.id)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
            )

        current_user.email = user_update.email.lower()
        current_user.is_verified = False

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/me/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change user password.

    Args:
        password_change: Password change data
        current_user: The authenticated user
        db: Database session

    Returns:
        dict: Success message
    """
    # Verify current password
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_change.new_password)
    await db.commit()

    return {"message": "Password updated successfully"}


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Delete user account and all associated data.

    Args:
        current_user: The authenticated user
        db: Database session

    Returns:
        dict: Success message
    """
    # Delete user (cascade will delete all related data)
    await db.delete(current_user)
    await db.commit()

    return {"message": "Account deleted successfully"}


@router.get("/me/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get user preferences.

    Args:
        current_user: The authenticated user
        db: Database session

    Returns:
        UserPreferences: User preferences
    """
    result = await db.execute(
        select(UserPrefsModel).where(UserPrefsModel.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()

    if not preferences:
        # Create default preferences if they don't exist
        preferences = UserPrefsModel(user_id=current_user.id)
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)

    return preferences


@router.patch("/me/preferences", response_model=UserPreferences)
async def update_user_preferences(
    prefs_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user preferences.

    Args:
        prefs_update: Preferences update data
        current_user: The authenticated user
        db: Database session

    Returns:
        UserPreferences: Updated preferences
    """
    result = await db.execute(
        select(UserPrefsModel).where(UserPrefsModel.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()

    if not preferences:
        preferences = UserPrefsModel(user_id=current_user.id)
        db.add(preferences)

    # Update fields
    update_data = prefs_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)

    await db.commit()
    await db.refresh(preferences)

    return preferences


@router.get("/me/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get user statistics.

    Args:
        current_user: The authenticated user
        db: Database session

    Returns:
        dict: User statistics
    """
    # Count total recipes
    result = await db.execute(
        select(func.count(Recipe.id)).where(
            Recipe.user_id == current_user.id, Recipe.deleted_at.is_(None)
        )
    )
    total_recipes = result.scalar()

    # Count imported recipes
    result = await db.execute(
        select(func.count(Recipe.id)).where(
            Recipe.user_id == current_user.id,
            Recipe.source_type == "imported",
            Recipe.deleted_at.is_(None),
        )
    )
    imported_recipes = result.scalar()

    # Count manual recipes
    manual_recipes = total_recipes - imported_recipes

    # Count collections
    result = await db.execute(
        select(func.count(Collection.id)).where(Collection.user_id == current_user.id)
    )
    total_collections = result.scalar()

    # Count trashed recipes
    result = await db.execute(
        select(func.count(Recipe.id)).where(
            Recipe.user_id == current_user.id, Recipe.deleted_at.isnot(None)
        )
    )
    trashed_recipes = result.scalar()

    return {
        "total_recipes": total_recipes,
        "imported_recipes": imported_recipes,
        "manual_recipes": manual_recipes,
        "total_collections": total_collections,
        "trashed_recipes": trashed_recipes,
        "account_created": current_user.created_at,
    }
