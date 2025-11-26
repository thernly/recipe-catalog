"""add_performance_indexes

Revision ID: 291505919b8f
Revises: 20251122_invite_links
Create Date: 2025-11-24 13:36:16.626930+00:00

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "291505919b8f"
down_revision: str | None = "20251122_invite_links"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add composite indexes for common query patterns."""
    # Composite index for filtering recipes by household and soft-delete status
    # Used in queries like: SELECT * FROM recipes WHERE household_id = ? AND deleted_at IS NULL
    op.create_index("idx_recipes_household_deleted", "recipes", ["household_id", "deleted_at"])

    # Composite index for sorting recipes by creation date within a household
    # Used in queries like: SELECT * FROM recipes WHERE household_id = ? ORDER BY created_at DESC
    op.create_index("idx_recipes_household_created", "recipes", ["household_id", "created_at"])


def downgrade() -> None:
    """Remove the composite indexes."""
    op.drop_index("idx_recipes_household_created", table_name="recipes")
    op.drop_index("idx_recipes_household_deleted", table_name="recipes")
