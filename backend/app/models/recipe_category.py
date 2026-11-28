"""Recipe category model.

One row per category a recipe belongs to ("Soup" and "Dinner" are two rows). The
rows are the filter index; `recipe_data["recipeCategory"]` is kept equal to them so
schema.org export/import round-trips. Write both through `services.categories`.
"""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecipeCategory(Base):
    """A category a recipe belongs to."""

    __tablename__ = "recipe_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))

    __table_args__ = (UniqueConstraint("recipe_id", "name", name="uq_recipe_categories_name"),)
