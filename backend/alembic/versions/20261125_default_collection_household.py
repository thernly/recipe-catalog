"""Give collections without a household their owner's household

The "Favorites" collection created at sign-up was stored with no household.
Collections are listed by household, so it never appeared until its owner
joined another household (which assigns one). Each such collection gets the
household its owner belongs to.

Revision ID: 20261125_default_coll_household
Revises: 20261125_refresh_ua
"""

from alembic import op


revision = "20261125_default_coll_household"
down_revision = "20261125_refresh_ua"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE collections SET household_id = (
            SELECT hm.household_id FROM household_members hm
            WHERE hm.user_id = collections.user_id
            LIMIT 1
        )
        WHERE household_id IS NULL
        """
    )


def downgrade() -> None:
    # The rows that were NULL can't be told apart afterwards; a household is harmless.
    pass
