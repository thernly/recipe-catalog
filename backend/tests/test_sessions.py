"""Active sessions list and revoke (issue #434)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.security import hash_token
from app.models.refresh_token import RefreshToken
from app.models.user import User


URL = "/api/v1/users/me/sessions"
EMAIL = "testuser@example.com"


async def _user_id(test_db) -> int:
    return (await test_db.execute(select(User.id).where(User.email == EMAIL))).scalar_one()


async def _add(test_db, user_id, raw, **kw) -> RefreshToken:
    row = RefreshToken(
        token=hash_token(raw),
        user_id=user_id,
        expires_at=kw.pop("expires_at", datetime.now(UTC) + timedelta(days=1)),
        **kw,
    )
    test_db.add(row)
    await test_db.commit()
    return row


async def test_list_shows_live_sessions_and_marks_current(client, test_db, test_user_headers):
    user_id = await _user_id(test_db)
    await _add(test_db, user_id, "gone", expires_at=datetime.now(UTC) - timedelta(minutes=1))
    await _add(test_db, user_id, "out", revoked=True, revoked_at=datetime.now(UTC))

    r = await client.get(URL, headers=test_user_headers)

    assert r.status_code == 200
    sessions = r.json()
    # Registration and login each started a session; the expired and revoked rows are hidden.
    assert len(sessions) == 2
    assert [s["current"] for s in sessions].count(True) == 1
    # The test client's User-Agent was recorded at registration and login.
    assert all(s["user_agent"] for s in sessions)


async def test_revoke_signs_that_session_out(client, test_db, test_user_headers):
    current = next(
        s for s in (await client.get(URL, headers=test_user_headers)).json() if s["current"]
    )

    r = await client.delete(f"{URL}/{current['id']}", headers=test_user_headers)

    assert r.status_code == 204
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401
    again = await client.delete(f"{URL}/{current['id']}", headers=test_user_headers)
    assert again.status_code == 404


async def test_cannot_revoke_another_users_session(client, test_db, test_user, test_user_headers):
    other = await _add(test_db, test_user.id, "someone-else")

    r = await client.delete(f"{URL}/{other.id}", headers=test_user_headers)

    assert r.status_code == 404
    await test_db.refresh(other)
    assert other.revoked is False


async def test_refresh_keeps_the_sessions_user_agent(client, test_db, test_user_headers):
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) Firefox/140.0"
    client.cookies.clear()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL, "password": "SecurePass123!"},
        headers={"User-Agent": ua},
    )
    assert login.status_code == 200

    refreshed = await client.post("/api/v1/auth/refresh", headers={"User-Agent": "other"})

    assert refreshed.status_code == 200
    row = (
        await test_db.execute(
            select(RefreshToken).where(
                RefreshToken.token == hash_token(refreshed.cookies["refresh_token"])
            )
        )
    ).scalar_one()
    assert row.user_agent == ua
