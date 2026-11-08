"""Keep email changes pending until address ownership is verified."""

import sqlalchemy as sa

from alembic import op


revision = "20261107_pending_email"
down_revision = "20261004_api_tokens"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("verification_tokens", sa.Column("pending_email", sa.String(255), nullable=True))


def downgrade():
    with op.batch_alter_table("verification_tokens") as batch:
        batch.drop_column("pending_email")
