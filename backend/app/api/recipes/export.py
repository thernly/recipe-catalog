"""
Single recipe export operations.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_user_household
from app.models.household import Household
from app.models.recipe import Recipe
from app.models.user import User
from app.services.recipe_export import RecipeExporter


router = APIRouter()


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
