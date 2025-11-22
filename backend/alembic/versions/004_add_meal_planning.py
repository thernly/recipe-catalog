"""add_meal_planning

Revision ID: 004_meal_planning
Revises: 003_household_support
Create Date: 2025-11-18 00:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "004_meal_planning"
down_revision: str | None = "003_household_support"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create meal_plans table
    op.create_table(
        "meal_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("household_id", "week_start_date", name="uq_household_week"),
    )
    op.create_index(op.f("ix_meal_plans_id"), "meal_plans", ["id"], unique=False)
    op.create_index(
        op.f("ix_meal_plans_household_id"), "meal_plans", ["household_id"], unique=False
    )
    op.create_index(
        op.f("ix_meal_plans_week_start_date"),
        "meal_plans",
        ["week_start_date"],
        unique=False,
    )

    # Create planned_meals table
    op.create_table(
        "planned_meals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meal_plan_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("meal_type", sa.String(20), nullable=False),
        sa.Column("servings", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["meal_plan_id"], ["meal_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planned_meals_id"), "planned_meals", ["id"], unique=False)
    op.create_index(
        op.f("ix_planned_meals_meal_plan_id"),
        "planned_meals",
        ["meal_plan_id"],
        unique=False,
    )
    op.create_index(
        "ix_planned_meals_day_meal",
        "planned_meals",
        ["meal_plan_id", "day_of_week", "meal_type"],
        unique=False,
    )


def downgrade() -> None:
    # Drop planned_meals table
    op.drop_index("ix_planned_meals_day_meal", table_name="planned_meals")
    op.drop_index(op.f("ix_planned_meals_meal_plan_id"), table_name="planned_meals")
    op.drop_index(op.f("ix_planned_meals_id"), table_name="planned_meals")
    op.drop_table("planned_meals")

    # Drop meal_plans table
    op.drop_index(op.f("ix_meal_plans_week_start_date"), table_name="meal_plans")
    op.drop_index(op.f("ix_meal_plans_household_id"), table_name="meal_plans")
    op.drop_index(op.f("ix_meal_plans_id"), table_name="meal_plans")
    op.drop_table("meal_plans")
