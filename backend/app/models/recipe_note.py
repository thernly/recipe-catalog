"""Recipe note model.

A dated note a household member leaves on a recipe ("halved the sugar, still sweet").
Notes live in their own table, not in `recipe_data`, so recipe edits and re-imports,
which replace `recipe_data` wholesale, never touch them.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.core.database import Base
from app.models._utils import utc_now
from app.models.recipe import Recipe


MAX_NOTE_LENGTH = 10000


class RecipeNote(Base):
    """A note on a recipe, written by a household member."""

    __tablename__ = "recipe_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    # The account that added the note (for an imported note, the importing user).
    # NULL once that account is deleted; the note stays, under its saved author_name.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    # Shown instead of the live name lookup. Set for imported notes (the original
    # author) and when the author's account is deleted (their last name).
    author_name: Mapped[str | None] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    # Set when the author edits the note
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    recipe = relationship("Recipe", back_populates="notes")
    user = relationship("User", back_populates="recipe_notes")


def live_author_name(user: Any) -> str:
    """A user's display name, else the part of their email before "@"."""
    return str(user.display_name or "") or str(user.email).split("@", 1)[0]


def note_author_name(note: RecipeNote) -> str:
    """The name a note is shown under. Needs `note.user` loaded.

    A saved name (imported note, or deleted author) wins; otherwise look it up live.
    """
    if note.author_name:
        return note.author_name
    return live_author_name(note.user) if note.user else "Former member"


def load_recipe_notes() -> ExecutableOption:
    """Eager-load a recipe's notes and their authors.

    Async sessions cannot lazy-load: add this to any Recipe query whose results are
    exported (convert_to_schema_org reads recipe.notes and each note's user). A
    function, not a constant, so the mappers are configured only once all models exist.
    """
    return selectinload(Recipe.notes).selectinload(RecipeNote.user)
