"""add_oauth_state_storage

Revision ID: 20251118_oauth_state
Revises: 20251118_add_dietary_preferences
Create Date: 2025-11-18 05:00:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251118_oauth_state"
down_revision: Union[str, None] = "20251118_dietary"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create oauth_states table for secure state storage."""
    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_oauth_states_id"), "oauth_states", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_oauth_states_token"), "oauth_states", ["token"], unique=True
    )


def downgrade() -> None:
    """Drop oauth_states table."""
    op.drop_index(op.f("ix_oauth_states_token"), table_name="oauth_states")
    op.drop_index(op.f("ix_oauth_states_id"), table_name="oauth_states")
    op.drop_table("oauth_states")
