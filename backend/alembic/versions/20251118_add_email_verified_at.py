"""add email_verified_at to users

Revision ID: 20251118_add_email_verified_at
Revises: 20251118_merge_heads
Create Date: 2025-11-18 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251118_add_email_verified_at"
down_revision: Union[str, None] = "20251118_merge_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add email_verified_at column to users table."""
    # SQLite doesn't support ALTER COLUMN, so we add the column
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove email_verified_at column from users table."""
    # For SQLite, we would need to recreate the table to remove a column
    # But for this migration, we'll use a simple drop column approach
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("email_verified_at")
