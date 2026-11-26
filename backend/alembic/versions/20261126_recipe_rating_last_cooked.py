"""Add a household rating and a last-cooked date to recipes

Both are optional and shared by the household. Existing recipes stay unrated and
never cooked.

Revision ID: 20261126_rating_last_cooked
Revises: 20261125_default_coll_household
"""

import sqlalchemy as sa

from alembic import op


revision = "20261126_rating_last_cooked"
down_revision = "20261125_default_coll_household"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("recipes") as batch:
        batch.add_column(sa.Column("rating", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("last_cooked_on", sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("recipes") as batch:
        batch.drop_column("last_cooked_on")
        batch.drop_column("rating")
