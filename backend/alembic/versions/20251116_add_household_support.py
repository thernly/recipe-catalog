"""add_household_support

Revision ID: 003_household_support
Revises: 002_idp_support
Create Date: 2025-11-16 12:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "003_household_support"
down_revision: str | None = "002_idp_support"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create households table
    op.create_table(
        "households",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("max_members", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_households_id"), "households", ["id"], unique=False)
    op.create_index(
        op.f("ix_households_owner_user_id"),
        "households",
        ["owner_user_id"],
        unique=False,
    )

    # Create household_members table
    op.create_table(
        "household_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("household_id", "user_id", name="uq_household_user"),
    )
    op.create_index(op.f("ix_household_members_id"), "household_members", ["id"], unique=False)
    op.create_index(
        op.f("ix_household_members_household_id"),
        "household_members",
        ["household_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_household_members_user_id"),
        "household_members",
        ["user_id"],
        unique=False,
    )

    # Create household_invitations table
    op.create_table(
        "household_invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("inviter_user_id", sa.Integer(), nullable=False),
        sa.Column("invitee_email", sa.String(255), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inviter_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_household_invitations_id"),
        "household_invitations",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_household_invitations_household_id"),
        "household_invitations",
        ["household_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_household_invitations_invitee_email"),
        "household_invitations",
        ["invitee_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_household_invitations_token"),
        "household_invitations",
        ["token"],
        unique=True,
    )

    # Add household_id to recipes table
    with op.batch_alter_table("recipes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("household_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_recipes_household_id", "households", ["household_id"], ["id"]
        )
        batch_op.create_index("ix_recipes_household_id", ["household_id"], unique=False)

    # Add household_id to collections table
    with op.batch_alter_table("collections", schema=None) as batch_op:
        batch_op.add_column(sa.Column("household_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_collections_household_id", "households", ["household_id"], ["id"]
        )
        batch_op.create_index("ix_collections_household_id", ["household_id"], unique=False)

    # Create "Personal Household" for existing users and migrate their data
    # This is done via SQL to ensure atomicity
    op.execute("""
        INSERT INTO households (name, owner_user_id, max_members, created_at, updated_at)
        SELECT
            'Personal Household',
            id,
            10,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM users;
    """)

    # Add household members for all users (owner role)
    op.execute("""
        INSERT INTO household_members (household_id, user_id, role, joined_at)
        SELECT
            h.id,
            h.owner_user_id,
            'owner',
            CURRENT_TIMESTAMP
        FROM households h;
    """)

    # Migrate existing recipes to household scope
    op.execute("""
        UPDATE recipes
        SET household_id = (
            SELECT h.id
            FROM households h
            WHERE h.owner_user_id = recipes.user_id
            LIMIT 1
        )
        WHERE household_id IS NULL;
    """)

    # Migrate existing collections to household scope
    op.execute("""
        UPDATE collections
        SET household_id = (
            SELECT h.id
            FROM households h
            WHERE h.owner_user_id = collections.user_id
            LIMIT 1
        )
        WHERE household_id IS NULL;
    """)


def downgrade() -> None:
    # Remove household_id from collections
    with op.batch_alter_table("collections", schema=None) as batch_op:
        batch_op.drop_index("ix_collections_household_id")
        batch_op.drop_constraint("fk_collections_household_id", type_="foreignkey")
        batch_op.drop_column("household_id")

    # Remove household_id from recipes
    with op.batch_alter_table("recipes", schema=None) as batch_op:
        batch_op.drop_index("ix_recipes_household_id")
        batch_op.drop_constraint("fk_recipes_household_id", type_="foreignkey")
        batch_op.drop_column("household_id")

    # Drop household_invitations table
    op.drop_index(op.f("ix_household_invitations_token"), table_name="household_invitations")
    op.drop_index(
        op.f("ix_household_invitations_invitee_email"),
        table_name="household_invitations",
    )
    op.drop_index(
        op.f("ix_household_invitations_household_id"),
        table_name="household_invitations",
    )
    op.drop_index(op.f("ix_household_invitations_id"), table_name="household_invitations")
    op.drop_table("household_invitations")

    # Drop household_members table
    op.drop_index(op.f("ix_household_members_user_id"), table_name="household_members")
    op.drop_index(op.f("ix_household_members_household_id"), table_name="household_members")
    op.drop_index(op.f("ix_household_members_id"), table_name="household_members")
    op.drop_table("household_members")

    # Drop households table
    op.drop_index(op.f("ix_households_owner_user_id"), table_name="households")
    op.drop_index(op.f("ix_households_id"), table_name="households")
    op.drop_table("households")
