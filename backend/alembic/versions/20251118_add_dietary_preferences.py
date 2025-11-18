"""add_dietary_preferences

Revision ID: 20251118_dietary
Revises: 006
Create Date: 2025-11-18 00:00:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251118_dietary"
down_revision: Union[str, None] = "006_update_theme_preferences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add dietary_preferences column to user_preferences table
    op.add_column(
        "user_preferences",
        sa.Column("dietary_preferences", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    # Remove dietary_preferences column from user_preferences table
    op.drop_column("user_preferences", "dietary_preferences")
