"""add household invite links

Revision ID: 20251122_invite_links
Revises: 20251118_add_email_verified_at
Create Date: 2025-11-22 20:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20251122_invite_links"
down_revision: str | None = "20251118_add_email_verified_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create household_invite_links table
    op.create_table(
        "household_invite_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("used_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["used_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_household_invite_links_id"),
        "household_invite_links",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_household_invite_links_household_id"),
        "household_invite_links",
        ["household_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_household_invite_links_code"),
        "household_invite_links",
        ["code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_household_invite_links_code"), table_name="household_invite_links")
    op.drop_index(
        op.f("ix_household_invite_links_household_id"),
        table_name="household_invite_links",
    )
    op.drop_index(op.f("ix_household_invite_links_id"), table_name="household_invite_links")
    op.drop_table("household_invite_links")
