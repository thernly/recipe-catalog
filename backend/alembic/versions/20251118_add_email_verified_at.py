"""add email_verified_at to users

Revision ID: 20251118_add_email_verified_at
Revises: 20251118_merge_heads
Create Date: 2025-11-18 13:00:00.000000

"""

from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "20251118_add_email_verified_at"
down_revision: str | None = "20251118_merge_heads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """email_verified_at was already introduced by 002_idp_support."""
    pass


def downgrade() -> None:
    """Leave the column in place until 002_idp_support is rolled back."""
    pass
