"""Signing up with a password sends a verification email."""

from unittest.mock import AsyncMock, patch


SIGNUP = {"email": "new@example.com", "password": "SecurePass123!", "display_name": "New"}


async def test_signup_sends_a_working_verification_link(client):
    with patch(
        "app.core.email.email_service.send_verification_email", new_callable=AsyncMock
    ) as send:
        registered = await client.post("/api/v1/auth/register", json=SIGNUP)
    assert registered.status_code == 201, registered.text
    assert registered.json()["is_verified"] is False

    send.assert_awaited_once()
    assert send.call_args.kwargs["to_email"] == "new@example.com"
    verified = await client.post(
        f"/api/v1/auth/verify-email/{send.call_args.kwargs['verification_token']}"
    )
    assert verified.status_code == 200, verified.text

    login = await client.post(
        "/api/v1/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]}
    )
    headers = {"Authorization": f"Bearer {login.cookies.get('access_token')}"}
    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.json()["is_verified"] is True


async def test_signup_succeeds_when_the_email_cannot_be_sent(client):
    with patch(
        "app.core.email.email_service.send_verification_email",
        new_callable=AsyncMock,
        side_effect=RuntimeError("smtp down"),
    ):
        registered = await client.post("/api/v1/auth/register", json=SIGNUP)
    assert registered.status_code == 201, registered.text
