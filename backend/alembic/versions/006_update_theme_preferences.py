"""Update theme preferences to new values

Revision ID: 006_update_theme_preferences
Revises: 005_shopping_lists
Create Date: 2025-11-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_update_theme_preferences'
down_revision = '005_shopping_lists'
branch_labels = None
depends_on = None


def upgrade():
    """Update existing theme preferences from 'classic' to 'light'."""
    # Update any existing 'classic' theme preferences to 'light'
    op.execute("""
        UPDATE user_preferences
        SET theme = 'light'
        WHERE theme = 'classic'
    """)


def downgrade():
    """Revert theme preferences from 'light' back to 'classic'."""
    # Revert 'light' theme preferences back to 'classic'
    op.execute("""
        UPDATE user_preferences
        SET theme = 'classic'
        WHERE theme = 'light'
    """)
