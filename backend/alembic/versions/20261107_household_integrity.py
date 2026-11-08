"""Preserve personal data ownership, hash invitation secrets, and reconcile legacy FKs.

Downgrading cannot reconstruct invitation secrets; pending invitations must be
reissued if the application is rolled back to a plaintext-token release.
"""

import hashlib

import sqlalchemy as sa

from alembic import op


revision = "20261107_household_integrity"
down_revision = "20261107_pending_email"
branch_labels = None
depends_on = None

_FK_TABLES = (
    "households",
    "household_members",
    "household_invitations",
    "household_invite_links",
    "meal_plans",
    "planned_meals",
    "shopping_lists",
    "shopping_list_items",
)


def upgrade():
    op.add_column(
        "households",
        sa.Column("is_personal", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    with op.batch_alter_table("planned_meals") as batch:
        batch.add_column(sa.Column("created_by_user_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_planned_meals_creator", "users", ["created_by_user_id"], ["id"], ondelete="SET NULL"
        )
    # Per-meal authorship is unknown; credit the plan creator only while they are
    # still in the plan's household, so a departed creator never claims the meals.
    op.execute("""
        UPDATE planned_meals SET created_by_user_id = (
            SELECT mp.created_by_user_id FROM meal_plans mp
            JOIN household_members hm
              ON hm.household_id = mp.household_id AND hm.user_id = mp.created_by_user_id
            WHERE mp.id = planned_meals.meal_plan_id
        )
    """)
    with op.batch_alter_table("household_invite_links") as batch:
        batch.alter_column("code", existing_type=sa.String(32), type_=sa.String(128))
    bind = op.get_bind()
    for row in list(
        bind.execute(sa.text("SELECT id, token FROM household_invitations")).mappings()
    ):
        bind.execute(
            sa.text("UPDATE household_invitations SET token = :token WHERE id = :id"),
            {"id": row["id"], "token": hashlib.sha256(row["token"].encode()).hexdigest()},
        )
    # Metadata-created databases missed the published migrations' deletion rules.
    # Preserve cascading cleanup, especially for dependents with no ORM relationship.
    for table in _FK_TABLES:
        fks = sa.inspect(bind).get_foreign_keys(table)

        def desired_action(fk, table=table):
            if table == "household_invite_links" and fk["constrained_columns"] == [
                "used_by_user_id"
            ]:
                return "SET NULL"
            if table == "planned_meals" and fk["constrained_columns"] == ["created_by_user_id"]:
                return "SET NULL"
            return "CASCADE"

        changed = [fk for fk in fks if fk.get("options", {}).get("ondelete") != desired_action(fk)]
        if not changed:
            continue
        convention = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}
        with op.batch_alter_table(table, naming_convention=convention) as batch:
            for fk in changed:
                name = (
                    fk["name"]
                    or f"fk_{table}_{fk['constrained_columns'][0]}_{fk['referred_table']}"
                )
                batch.drop_constraint(name, type_="foreignkey")
                batch.create_foreign_key(
                    name,
                    fk["referred_table"],
                    fk["constrained_columns"],
                    fk["referred_columns"],
                    ondelete=desired_action(fk),
                )
    columns = {column["name"]: column for column in sa.inspect(bind).get_columns("oauth_states")}
    if not columns["created_at"]["nullable"]:
        with op.batch_alter_table("oauth_states") as batch:
            batch.alter_column("created_at", existing_type=sa.DateTime(), nullable=True)

    _repair_legacy_scope(bind)


def _repair_legacy_scope(bind):
    """Repair orphaned recipes and former-member data without losing planned meals."""
    membership = {}
    for row in bind.execute(
        sa.text("SELECT user_id, household_id FROM household_members ORDER BY id")
    ).mappings():
        membership.setdefault(row["user_id"], row["household_id"])
    for user_id in bind.execute(sa.text("SELECT id FROM users")).scalars():
        if user_id not in membership:
            household_id = bind.execute(
                sa.text("""
                INSERT INTO households (name, owner_user_id, max_members, is_personal, created_at, updated_at)
                VALUES ('Personal recipes', :user_id, 10, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) RETURNING id
            """),
                {"user_id": user_id},
            ).scalar_one()
            bind.execute(
                sa.text("""
                INSERT INTO household_members (household_id, user_id, role, joined_at)
                VALUES (:household_id, :user_id, 'owner', CURRENT_TIMESTAMP)
            """),
                {"household_id": household_id, "user_id": user_id},
            )
            membership[user_id] = household_id
    for user_id, household_id in membership.items():
        for table, owner in (
            ("recipes", "user_id"),
            ("collections", "user_id"),
            ("shopping_lists", "created_by_user_id"),
        ):
            bind.execute(
                sa.text(
                    f"UPDATE {table} SET household_id = :household_id WHERE {owner} = :user_id"
                ),
                {"household_id": household_id, "user_id": user_id},
            )
    # Meal plans are shared household data: they stay where they are. A plan whose
    # creator left is re-credited to a remaining member so a later departure of
    # that ex-member cannot pull it out of the household.
    plans = bind.execute(
        sa.text("SELECT id, household_id, created_by_user_id, week_start_date FROM meal_plans")
    ).mappings()
    for plan in list(plans):
        if membership.get(plan["created_by_user_id"]) == plan["household_id"]:
            continue
        owner = bind.execute(
            sa.text("SELECT owner_user_id FROM households WHERE id = :id"),
            {"id": plan["household_id"]},
        ).scalar()
        resident = (
            owner
            if membership.get(owner) == plan["household_id"]
            else next(
                (uid for uid, scope in membership.items() if scope == plan["household_id"]),
                None,
            )
        )
        if resident is not None:
            bind.execute(
                sa.text("UPDATE meal_plans SET created_by_user_id = :user_id WHERE id = :id"),
                {"user_id": resident, "id": plan["id"]},
            )
            continue
        # Nobody is left to see the plan: it follows its creator, if they have a household.
        household_id = membership.get(plan["created_by_user_id"])
        if household_id is None:
            continue
        destination = bind.execute(
            sa.text(
                "SELECT id FROM meal_plans WHERE household_id = :household_id"
                " AND week_start_date = :week"
            ),
            {"household_id": household_id, "week": plan["week_start_date"]},
        ).scalar()
        if destination is None:
            bind.execute(
                sa.text("UPDATE meal_plans SET household_id = :household_id WHERE id = :id"),
                {"household_id": household_id, "id": plan["id"]},
            )
        else:
            bind.execute(
                sa.text("UPDATE planned_meals SET meal_plan_id = :dest WHERE meal_plan_id = :id"),
                {"dest": destination, "id": plan["id"]},
            )
            bind.execute(sa.text("DELETE FROM meal_plans WHERE id = :id"), {"id": plan["id"]})
    bind.execute(
        sa.text("""
        DELETE FROM recipe_collections WHERE id IN (
            SELECT rc.id FROM recipe_collections rc
            JOIN recipes r ON r.id = rc.recipe_id
            JOIN collections c ON c.id = rc.collection_id
            WHERE r.household_id != c.household_id
        )
    """)
    )


def downgrade():
    with op.batch_alter_table("planned_meals") as batch:
        batch.drop_constraint("fk_planned_meals_creator", type_="foreignkey")
        batch.drop_column("created_by_user_id")
    with op.batch_alter_table("household_invite_links") as batch:
        batch.alter_column("code", existing_type=sa.String(128), type_=sa.String(32))
    op.drop_column("households", "is_personal")
