"""Regression tests for household migration repair, personal-household cleanup and invite links."""

import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.models.household import Household, HouseholdInvitation, HouseholdMember
from app.models.recipe import Recipe
from app.models.user import User
from app.services import household as household_service


def test_upgrade_keeps_meals_when_plan_creator_left(tmp_path):
    """A creates the plan, B and C add meals, A leaves: the meals stay with B and C."""
    backend_dir = Path(__file__).resolve().parents[1]
    database = tmp_path / "legacy.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{database}", "DEBUG": "false"}

    def migrate(*arguments):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    migrate("upgrade", "20261004_api_tokens")
    with sqlite3.connect(database) as connection:
        for user_id in (1, 2, 3):
            connection.execute(
                """INSERT INTO users
                (id,email,is_active,is_verified,created_at,updated_at,failed_login_attempts)
                VALUES (?,?,1,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,0)""",
                (user_id, f"u{user_id}@example.com"),
            )
        # Household 1 is shared by B (2, owner) and C (3); A (1) has moved to household 2.
        for household_id, owner in ((1, 2), (2, 1)):
            connection.execute(
                """INSERT INTO households
                (id,name,owner_user_id,max_members,created_at,updated_at)
                VALUES (?,'H',?,10,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)""",
                (household_id, owner),
            )
        for user_id, household_id in ((1, 2), (2, 1), (3, 1)):
            connection.execute(
                """INSERT INTO household_members (user_id,household_id,role,joined_at)
                VALUES (?,?,'member',CURRENT_TIMESTAMP)""",
                (user_id, household_id),
            )
        connection.execute(
            """INSERT INTO recipes
            (id,user_id,household_id,name,recipe_data,source_type,is_modified,created_at,updated_at)
            VALUES (1,2,1,'Soup','{}','manual',0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"""
        )
        connection.execute(
            """INSERT INTO meal_plans
            (id,household_id,created_by_user_id,week_start_date,created_at,updated_at)
            VALUES (1,1,1,'2026-11-02',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"""
        )
        for meal_id in (1, 2):
            connection.execute(
                """INSERT INTO planned_meals
                (id,meal_plan_id,recipe_id,day_of_week,meal_type,created_at,updated_at)
                VALUES (?,1,1,?,'dinner',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)""",
                (meal_id, meal_id),
            )
    migrate("upgrade", "head")
    with sqlite3.connect(database) as connection:
        assert list(
            connection.execute("""SELECT pm.id,mp.id,mp.household_id,pm.created_by_user_id
            FROM planned_meals pm JOIN meal_plans mp ON mp.id=pm.meal_plan_id ORDER BY pm.id""")
        ) == [(1, 1, 1, None), (2, 1, 1, None)]
        # Re-credited to the remaining owner so A joining elsewhere cannot pull the plan out.
        assert connection.execute("SELECT created_by_user_id FROM meal_plans").fetchall() == [(2,)]
    migrate("downgrade", "20261107_pending_email")


async def test_joining_removes_empty_personal_household(db, test_user, test_household):
    joiner = User(email="joiner@example.com", is_active=True, is_verified=True)
    db.add(joiner)
    await db.flush()
    personal = Household(
        name="Personal recipes", owner_user_id=joiner.id, max_members=10, is_personal=True
    )
    db.add(personal)
    await db.flush()
    db.add(HouseholdMember(household_id=personal.id, user_id=joiner.id, role="owner"))
    db.add(
        Recipe(
            user_id=joiner.id,
            household_id=personal.id,
            name="Mine",
            recipe_data={},
            source_type="manual",
        )
    )
    await db.commit()
    personal_id = personal.id

    link = await household_service.create_invite_link(db, test_household["id"], test_user.id)
    await household_service.join_via_invite_link(db, link.code, joiner.id)

    db.expunge_all()
    assert await db.get(Household, personal_id) is None
    recipe = (await db.execute(select(Recipe).where(Recipe.user_id == joiner.id))).scalar_one()
    assert recipe.household_id == test_household["id"]


async def test_invitation_email_links_to_path_route(db, test_user, test_household, monkeypatch):
    sent = []

    async def fake_send(to_email, subject, html_body, body):
        sent.append(body)

    monkeypatch.setattr(household_service.email_service, "send_email", fake_send)
    invitation = HouseholdInvitation(
        household_id=test_household["id"],
        inviter_user_id=test_user.id,
        invitee_email="x@example.com",
        token="hashed",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    invitation.raw_token = "a/b c"
    await household_service.send_invitation_email(db, invitation)
    assert f"{settings.FRONTEND_URL}/invitations/accept/a%2Fb%20c" in sent[0]
