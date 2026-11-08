"""Mark existing solo households as personal

Registration households were created with is_personal = false, which blocked
their users from accepting an invitation to another household. A household
whose only member is its owner, with no outstanding invitation or invite link,
is marked personal so its user can join elsewhere.

Revision ID: 20261107_solo_households_personal
Revises: 20261107_drop_legacy_ms_links
"""

from alembic import op


revision = "20261107_solo_households_personal"
down_revision = "20261107_drop_legacy_ms_links"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE households SET is_personal = 1
        WHERE is_personal = 0
          AND (SELECT COUNT(*) FROM household_members hm
               WHERE hm.household_id = households.id) = 1
          AND EXISTS (SELECT 1 FROM household_members hm
                      WHERE hm.household_id = households.id
                        AND hm.user_id = households.owner_user_id)
          AND NOT EXISTS (SELECT 1 FROM household_invitations i
                          WHERE i.household_id = households.id
                            AND i.accepted_at IS NULL
                            AND i.expires_at > CURRENT_TIMESTAMP)
          AND NOT EXISTS (SELECT 1 FROM household_invite_links l
                          WHERE l.household_id = households.id
                            AND l.used_at IS NULL
                            AND l.expires_at > CURRENT_TIMESTAMP)
        """
    )


def downgrade() -> None:
    # Households created personal at registration can't be told apart; the flag is harmless.
    pass
