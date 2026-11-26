"""Let a planned meal be free text instead of a recipe

planned_meals.recipe_id becomes nullable and a title column is added, so a slot
can say "Leftovers" or "Eating out". A meal has a recipe or a title; the API
enforces that. Existing meals keep their recipe and get no title.

Revision ID: 20261126_planned_meal_title
Revises: 20261126_rating_last_cooked
"""

import sqlalchemy as sa

from alembic import op


revision = "20261126_planned_meal_title"
down_revision = "20261126_rating_last_cooked"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("planned_meals") as batch:
        batch.alter_column("recipe_id", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column("title", sa.String(length=200), nullable=True))


def downgrade() -> None:
    # A free-text meal has no recipe to point at; it cannot survive a NOT NULL recipe_id
    op.execute("DELETE FROM planned_meals WHERE recipe_id IS NULL")
    with op.batch_alter_table("planned_meals") as batch:
        batch.drop_column("title")
        batch.alter_column("recipe_id", existing_type=sa.Integer(), nullable=False)
