"""add foreign key to user_preferences

Revision ID: 001
Revises:
Create Date: 2025-11-15 13:35:00

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add foreign key constraint to user_preferences.user_id"""
    # For SQLite, we need to recreate the table to add a foreign key
    # This is because SQLite doesn't support ALTER TABLE ADD FOREIGN KEY

    # Check if we're using SQLite
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite approach: recreate the table
        # Note: This will preserve data
        with op.batch_alter_table("user_preferences") as batch_op:
            batch_op.create_foreign_key("fk_user_preferences_user_id", "users", ["user_id"], ["id"])
    else:
        # PostgreSQL/MySQL approach: directly add foreign key
        op.create_foreign_key(
            "fk_user_preferences_user_id",
            "user_preferences",
            "users",
            ["user_id"],
            ["id"],
        )


def downgrade():
    """Remove foreign key constraint from user_preferences.user_id"""
    with op.batch_alter_table("user_preferences") as batch_op:
        batch_op.drop_constraint("fk_user_preferences_user_id", type_="foreignkey")
