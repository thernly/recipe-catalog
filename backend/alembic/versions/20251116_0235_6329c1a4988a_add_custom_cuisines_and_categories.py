"""add_custom_cuisines_and_categories

Revision ID: 6329c1a4988a
Revises: 001
Create Date: 2025-11-16 02:35:34.124996+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6329c1a4988a"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add custom_cuisines and custom_categories columns to user_preferences table
    op.add_column(
        "user_preferences",
        sa.Column("custom_cuisines", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "user_preferences",
        sa.Column("custom_categories", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    # Remove custom_cuisines and custom_categories columns from user_preferences table
    op.drop_column("user_preferences", "custom_categories")
    op.drop_column("user_preferences", "custom_cuisines")
