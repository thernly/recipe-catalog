"""add_account_lockout_fields

Revision ID: 940142933e9f
Revises: 291505919b8f
Create Date: 2025-11-25 19:16:55.310648+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "940142933e9f"
down_revision: Union[str, None] = "291505919b8f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add account lockout fields to users table."""
    # Add failed_login_attempts column
    op.add_column(
        "users",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
    )

    # Add locked_until column
    op.add_column("users", sa.Column("locked_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove account lockout fields from users table."""
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
