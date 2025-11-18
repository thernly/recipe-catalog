"""add_shopping_lists

Revision ID: 005_shopping_lists
Revises: 004_meal_planning
Create Date: 2025-11-18 00:00:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005_shopping_lists"
down_revision: Union[str, None] = "004_meal_planning"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create shopping_lists table
    op.create_table(
        "shopping_lists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["household_id"], ["households.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_shopping_lists_id"), "shopping_lists", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_shopping_lists_household_id"),
        "shopping_lists",
        ["household_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shopping_lists_status"), "shopping_lists", ["status"], unique=False
    )

    # Create shopping_list_items table
    op.create_table(
        "shopping_list_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("list_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("quantity", sa.String(100), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("checked", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["list_id"], ["shopping_lists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_shopping_list_items_id"), "shopping_list_items", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_shopping_list_items_list_id"),
        "shopping_list_items",
        ["list_id"],
        unique=False,
    )
    op.create_index(
        "ix_shopping_list_items_checked",
        "shopping_list_items",
        ["list_id", "checked"],
        unique=False,
    )


def downgrade() -> None:
    # Drop shopping_list_items table
    op.drop_index("ix_shopping_list_items_checked", table_name="shopping_list_items")
    op.drop_index(
        op.f("ix_shopping_list_items_list_id"), table_name="shopping_list_items"
    )
    op.drop_index(op.f("ix_shopping_list_items_id"), table_name="shopping_list_items")
    op.drop_table("shopping_list_items")

    # Drop shopping_lists table
    op.drop_index(op.f("ix_shopping_lists_status"), table_name="shopping_lists")
    op.drop_index(op.f("ix_shopping_lists_household_id"), table_name="shopping_lists")
    op.drop_index(op.f("ix_shopping_lists_id"), table_name="shopping_lists")
    op.drop_table("shopping_lists")
