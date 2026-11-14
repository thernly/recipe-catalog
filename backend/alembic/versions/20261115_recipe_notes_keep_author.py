"""Keep recipe notes when their author's account is deleted

recipe_notes.user_id becomes nullable with ON DELETE SET NULL (was NOT NULL,
CASCADE). The account-deletion route saves the author's name into author_name
first, so the note keeps showing who wrote it.

Revision ID: 20261115_notes_keep_author
Revises: 20261114_recipe_notes
"""

import sqlalchemy as sa

from alembic import op


revision = "20261115_notes_keep_author"
down_revision = "20261114_recipe_notes"
branch_labels = None
depends_on = None

# The FK was created unnamed; batch mode needs a name to drop it on SQLite
_CONVENTION = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}
_FK = "fk_recipe_notes_user_id_users"


def upgrade() -> None:
    with op.batch_alter_table("recipe_notes", naming_convention=_CONVENTION) as batch:
        batch.drop_constraint(_FK, type_="foreignkey")
        batch.alter_column("user_id", existing_type=sa.Integer(), nullable=True)
        batch.create_foreign_key(_FK, "users", ["user_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    # Notes whose author was deleted have no account to point at; they cannot
    # survive a NOT NULL user_id
    op.execute("DELETE FROM recipe_notes WHERE user_id IS NULL")
    with op.batch_alter_table("recipe_notes", naming_convention=_CONVENTION) as batch:
        batch.drop_constraint(_FK, type_="foreignkey")
        batch.alter_column("user_id", existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key(_FK, "users", ["user_id"], ["id"], ondelete="CASCADE")
