"""merge oauth and refresh token heads

Revision ID: 20251118_merge_heads
Revises: 20251118_oauth_state, 20251118_add_refresh_tokens
Create Date: 2025-11-18 12:30:00.000000

"""

from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = "20251118_merge_heads"
down_revision: Union[str, Sequence[str], None] = ("20251118_oauth_state", "20251118_add_refresh_tokens")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration - no changes needed."""
    pass


def downgrade() -> None:
    """Merge migration - no changes needed."""
    pass
