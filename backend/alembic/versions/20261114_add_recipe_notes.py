"""Add recipe_notes table for dated notes on recipes

Revision ID: 20261114_recipe_notes
Revises: 20261107_solo_households_personal
Create Date: 2026-11-14 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20261114_recipe_notes"
down_revision: str | None = "20261107_solo_households_personal"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create recipe_notes table."""
    op.create_table(
        "recipe_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("author_name", sa.String(length=100), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recipe_notes_recipe_id"), "recipe_notes", ["recipe_id"], unique=False)
    op.create_index(op.f("ix_recipe_notes_user_id"), "recipe_notes", ["user_id"], unique=False)


def downgrade() -> None:
    """Drop recipe_notes table."""
    op.drop_index(op.f("ix_recipe_notes_user_id"), table_name="recipe_notes")
    op.drop_index(op.f("ix_recipe_notes_recipe_id"), table_name="recipe_notes")
    op.drop_table("recipe_notes")
