"""Recipe note schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.utils.recipe_format import plain_text


MAX_NOTE_LENGTH = 10000


class RecipeNoteWrite(BaseModel):
    """Body for adding or editing a note."""

    text: str = Field(..., max_length=MAX_NOTE_LENGTH)

    @field_validator("text")
    @classmethod
    def clean_text(cls, v: str) -> str:
        """Strip markup; store plain text (the frontend escapes on render)."""
        cleaned = plain_text(v)
        if not cleaned:
            raise ValueError("Note cannot be empty")
        return cleaned


class RecipeNoteResponse(BaseModel):
    """A note as returned to household members. Never includes an email address."""

    id: int
    recipe_id: int
    text: str
    author_name: str
    # True when the caller wrote the note, so the UI can offer editing
    is_author: bool
    created_at: datetime
    updated_at: datetime | None = None
