"""Follow-ups to the November review: timezone, login throttle, refresh reuse, sessions."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, text

from app.api import auth as auth_api
from app.core.security import hash_token
from app.models.identity_provider import IdentityProvider
from app.models.recipe import Recipe
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserPreferences


EMAIL = "testuser@example.com"
PASSWORD = "SecurePass123!"


@pytest.fixture(autouse=True)
def _clear_login_throttle():
    auth_api._login_failures.clear()
    yield
    auth_api._login_failures.clear()


async def _user(test_db) -> User:
    return (await test_db.execute(select(User).where(User.email == EMAIL))).scalar_one()


@pytest.mark.parametrize("legacy", ["PST", "Eastern", ""])
async def test_legacy_timezone_does_not_break_reads(client, test_db, test_user_headers, legacy):
    user = await _user(test_db)
    prefs = (
        await test_db.execute(select(UserPreferences).where(UserPreferences.user_id == user.id))
    ).scalar_one()
    prefs.timezone = legacy
    await test_db.commit()

    got = await client.get("/api/v1/users/me/preferences", headers=test_user_headers)
    assert got.status_code == 200
    assert got.json()["timezone"] == "UTC"
    current = await client.get("/api/v1/meal-plans/current", headers=test_user_headers)
    assert current.status_code == 200


async def test_timezone_input_validation(client, test_user_headers):
    url = "/api/v1/users/me/preferences"
    bad = await client.patch(url, headers=test_user_headers, json={"timezone": "PST"})
    assert bad.status_code == 422
    empty = await client.patch(url, headers=test_user_headers, json={"timezone": ""})
    assert empty.status_code == 200
    assert empty.json()["timezone"] == "UTC"
    ok = await client.patch(url, headers=test_user_headers, json={"timezone": "America/New_York"})
    assert ok.json()["timezone"] == "America/New_York"


async def test_per_account_login_throttle(client, test_user_headers, monkeypatch):
    monkeypatch.setattr(auth_api, "LOGIN_FAILURE_LIMIT", 3)
    for _ in range(3):
        r = await client.post(
            "/api/v1/auth/login", json={"email": EMAIL.upper(), "password": "wrong"}
        )
        assert r.status_code == 401
    blocked = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert blocked.status_code == 429
    # Other accounts are unaffected
    other = await client.post(
        "/api/v1/auth/login", json={"email": "other@example.com", "password": "x"}
    )
    assert other.status_code == 401
    # The window slides: once failures age out, the real user can sign in again.
    monkeypatch.setattr(auth_api, "LOGIN_FAILURE_WINDOW_S", 0)
    ok = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert ok.status_code == 200
    assert EMAIL not in auth_api._login_failures


async def test_long_password_can_log_in(client, test_db, test_user_headers):
    from app.core.security import get_password_hash

    long_password = "Aa1" + "x" * 200
    user = await _user(test_db)
    user.hashed_password = get_password_hash(long_password)
    await test_db.commit()
    r = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": long_password})
    assert r.status_code == 200


async def _add_refresh(test_db, user_id, value, revoked_at=None):
    test_db.add(
        RefreshToken(
            token=hash_token(value),
            user_id=user_id,
            expires_at=datetime.now(UTC) + timedelta(days=1),
            revoked=revoked_at is not None,
            revoked_at=revoked_at,
        )
    )
    await test_db.commit()


async def _active_count(test_db, user_id) -> int:
    rows = await test_db.execute(
        select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
    )
    return len(rows.scalars().all())


async def test_refresh_reuse_within_grace_window_is_benign(client, test_db, test_user_headers):
    user_id = (await _user(test_db)).id
    await _add_refresh(test_db, user_id, "just-rotated", revoked_at=datetime.now(UTC))
    before = await _active_count(test_db, user_id)
    assert before >= 1
    client.cookies.clear()
    client.cookies.set("refresh_token", "just-rotated")
    r = await client.post("/api/v1/auth/refresh")
    assert r.status_code == 401
    assert await _active_count(test_db, user_id) == before


async def test_refresh_reuse_after_grace_window_revokes_all(client, test_db, test_user_headers):
    user_id = (await _user(test_db)).id
    await _add_refresh(
        test_db, user_id, "old-stolen", revoked_at=datetime.now(UTC) - timedelta(minutes=5)
    )
    client.cookies.clear()
    client.cookies.set("refresh_token", "old-stolen")
    r = await client.post("/api/v1/auth/refresh")
    assert r.status_code == 401
    test_db.expire_all()
    assert await _active_count(test_db, user_id) == 0


async def test_password_change_keeps_current_session(client, test_db, test_user_headers):
    user_id = (await _user(test_db)).id
    await _add_refresh(test_db, user_id, "other-device")
    r = await client.post(
        "/api/v1/users/me/change-password",
        headers=test_user_headers,
        json={"current_password": PASSWORD, "new_password": "NewSecurePass456!"},
    )
    assert r.status_code == 200
    new_refresh = r.cookies.get("refresh_token")
    assert new_refresh and r.cookies.get("access_token") and r.cookies.get("csrf_token")
    test_db.expire_all()
    active = (
        (
            await test_db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)
                )
            )
        )
        .scalars()
        .all()
    )
    assert [t.token for t in active] == [hash_token(new_refresh)]
    client.cookies.clear()
    client.cookies.set("refresh_token", new_refresh)
    assert (await client.post("/api/v1/auth/refresh")).status_code == 200


async def test_meal_count_excludes_trashed_recipes(client, test_db, test_user_headers):
    ids = []
    for name in ("Kept", "Trashed"):
        r = await client.post(
            "/api/v1/recipes/", headers=test_user_headers, json={"name": name, "recipe_data": {}}
        )
        ids.append(r.json()["id"])
    plan = (await client.get("/api/v1/meal-plans/current", headers=test_user_headers)).json()
    for day, rid in enumerate(ids):
        r = await client.post(
            f"/api/v1/meal-plans/{plan['id']}/meals",
            headers=test_user_headers,
            json={"recipe_id": rid, "day_of_week": day, "meal_type": "dinner"},
        )
        assert r.status_code == 201
    trashed = await test_db.get(Recipe, ids[1])
    trashed.deleted_at = datetime.now(UTC)
    await test_db.commit()
    plans = (await client.get("/api/v1/meal-plans/", headers=test_user_headers)).json()
    assert [p["meal_count"] for p in plans if p["id"] == plan["id"]] == [1]


async def test_legacy_microsoft_links_migration(test_db, test_user, monkeypatch):
    import importlib.util
    from pathlib import Path

    path = Path(__file__).parents[1] / "alembic/versions/20261107_drop_legacy_microsoft_links.py"
    spec = importlib.util.spec_from_file_location("drop_ms_links", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    statements: list[str] = []
    monkeypatch.setattr(migration.op, "execute", statements.append, raising=False)
    migration.upgrade()
    assert len(statements) == 1

    for provider in ("microsoft", "google"):
        test_db.add(
            IdentityProvider(
                user_id=test_user.id,
                provider_name=provider,
                provider_subject=f"{provider}-sub",
                email_at_provider=test_user.email,
            )
        )
    await test_db.commit()
    await test_db.execute(text(statements[0]))
    await test_db.commit()
    rows = (await test_db.execute(select(IdentityProvider.provider_name))).scalars().all()
    assert rows == ["google"]
