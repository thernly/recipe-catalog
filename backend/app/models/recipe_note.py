"""Recipe note model.

A dated note a household member leaves on a recipe ("halved the sugar, still sweet").
Notes live in their own table, not in `recipe_data`, so recipe edits and re-imports,
which replace `recipe_data` wholesale, never touch them.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._utils import utc_now


class RecipeNote(Base):
    """A note on a recipe, written by a household member."""

    __tablename__ = "recipe_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    # The account that added the note (for an imported note, the importing user)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # Set only for imported notes: the original author's name, shown instead of the
    # live name lookup
    author_name: Mapped[str | None] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    # Set when the author edits the note
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    recipe = relationship("Recipe", back_populates="notes")
    user = relationship("User", back_populates="recipe_notes")
