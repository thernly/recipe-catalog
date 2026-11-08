"""Delete Microsoft identity-provider links created before the explicit link flow.

Microsoft's `email` claim is not verified, and the old callback auto-linked a Microsoft
account to any existing user with the same email, so any of these rows may be a takeover.
The old rows cannot be told apart from legitimate ones, and the explicit link flow has
never shipped, so every existing Microsoft link is removed. Users re-link from Settings;
Microsoft-only accounts (no password) recover via "forgot password" to their account email.
Downgrade cannot restore the rows.
"""

from alembic import op


revision = "20261107_drop_legacy_ms_links"
down_revision = "20261107_household_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM identity_providers WHERE provider_name = 'microsoft'")


def downgrade() -> None:
    pass
