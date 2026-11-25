"""Record the browser user agent on refresh tokens

Lets the active-sessions list show which device each session belongs to.
Existing rows stay NULL and show as an unknown device.

Revision ID: 20261125_refresh_ua
Revises: 20261115_notes_keep_author
"""

import sqlalchemy as sa

from alembic import op


revision = "20261125_refresh_ua"
down_revision = "20261115_notes_keep_author"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch:
        batch.add_column(sa.Column("user_agent", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch:
        batch.drop_column("user_agent")
