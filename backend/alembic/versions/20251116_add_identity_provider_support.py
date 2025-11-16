"""add_identity_provider_support

Revision ID: 002_idp_support
Revises: 6329c1a4988a
Create Date: 2025-11-16 00:00:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_idp_support"
down_revision: Union[str, None] = "6329c1a4988a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make hashed_password nullable in users table
    # SQLite doesn't support ALTER COLUMN directly, so we need to use a workaround
    # For SQLite, this will be handled by recreating the table
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "hashed_password", existing_type=sa.String(255), nullable=True
        )
        batch_op.add_column(
            sa.Column("email_verified_at", sa.DateTime(), nullable=True)
        )

    # Create identity_providers table
    op.create_table(
        "identity_providers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider_name", sa.String(50), nullable=False),
        sa.Column("provider_subject", sa.String(255), nullable=False),
        sa.Column("email_at_provider", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_identity_providers_id"), "identity_providers", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_identity_providers_user_id"),
        "identity_providers",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "uq_provider_subject",
        "identity_providers",
        ["provider_name", "provider_subject"],
        unique=True,
    )


def downgrade() -> None:
    # Drop identity_providers table and indexes
    op.drop_index("uq_provider_subject", table_name="identity_providers")
    op.drop_index(
        op.f("ix_identity_providers_user_id"), table_name="identity_providers"
    )
    op.drop_index(op.f("ix_identity_providers_id"), table_name="identity_providers")
    op.drop_table("identity_providers")

    # Remove email_verified_at and make hashed_password not nullable again
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("email_verified_at")
        batch_op.alter_column(
            "hashed_password", existing_type=sa.String(255), nullable=False
        )
