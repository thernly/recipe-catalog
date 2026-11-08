# OAuth / Identity Provider Authentication Setup

How to configure sign-in with Google, GitHub and Microsoft. Code: `backend/app/api/oauth.py`, `backend/app/core/oauth.py`, settings in `backend/app/core/config.py`.

## Overview

- **Google** and **GitHub** — sign in, sign up (passwordless account), and auto-link to an existing account when the provider has verified the email.
- **Microsoft** — link-only. Sign-up through Microsoft is off: a Microsoft login with no existing link is rejected with "Create and verify an account first, then link Microsoft in Settings", and Microsoft never auto-links by email. Migration `20261107_drop_legacy_microsoft_links` deleted all previously stored Microsoft links, so affected users must re-link from Settings.
- **Linking** — a signed-in, verified user can link any provider from Settings → Security (`frontend/src/lib/components/settings/SecuritySection.svelte`, `src/lib/api/oauth.ts`).

## Architecture

### Database

**`identity_providers`:** `id`, `user_id`, `provider_name` (google, microsoft, github), `provider_subject`, `email_at_provider`, `created_at`, `last_used_at`.

**`users`:** `hashed_password` is nullable (IdP-only accounts); `email_verified_at` records verification.

**`oauth_states`:** one-time, expiring state tokens (stored hashed) carrying the provider, an optional link target user and an optional validated return URL.

### API Endpoints

All under `/api/v1/auth`:

- `GET /providers` — list configured providers
- `GET /{provider}/authorize?return_url=&link=` — start the flow (10/minute per IP). `return_url` must pass `is_safe_redirect_url`; `link=true` requires a signed-in, verified user.
- `GET /{provider}/callback` — finish the flow (10/minute per IP)
- `GET /me/providers` — list the current user's linked providers
- `DELETE /providers/{id}` — unlink a provider

### Callback behavior

On success the callback sets the same cookies as password login: httpOnly `access_token` and `refresh_token` (a `refresh_tokens` row, so normal `/auth/refresh` works) plus a readable `csrf_token`. Then:

- Browser requests (`Accept` contains `text/html`) get a **303** redirect to the state's `return_url` if it is still safe, otherwise `FRONTEND_URL/dashboard`.
- Other clients get JSON `{"message": "Login successful", "csrf_token": "..."}`.

Resolution order: existing link for this provider subject → explicit link request → (Microsoft: reject) → verified-email auto-link to an existing user (Google/GitHub only) → create a new passwordless user with household, preferences and a Favorites collection.

## Provider Setup

Each provider's redirect URI is `{OAUTH_REDIRECT_BASE_URL}/{provider}/callback`, e.g. `http://localhost:8000/api/v1/auth/google/callback` in development.

### Google

1. [Google Cloud Console](https://console.cloud.google.com/) → Credentials → Create OAuth 2.0 Client ID (Web application).
2. Consent screen scopes: `openid`, `email`, `profile`.
3. Add the redirect URI; copy the client ID and secret into `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`.

### GitHub

1. [GitHub Developer Settings](https://github.com/settings/developers) → New OAuth App.
2. Authorization callback URL: the redirect URI above.
3. Copy the client ID and secret into `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`.

### Microsoft (link-only)

1. [Azure Portal](https://portal.azure.com/) → App registrations → New registration; supported account types "any organizational directory and personal Microsoft accounts"; Web redirect URI as above.
2. Certificates & secrets → New client secret.
3. API permissions: Microsoft Graph delegated `openid`, `email`, `profile`.
4. Set `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET`.

## Configuration

`backend/.env`:

```bash
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Auth API base; provider redirect URIs are {this}/{provider}/callback
OAUTH_REDIRECT_BASE_URL=http://localhost:8000/api/v1/auth

# Where browsers land after a successful callback (/dashboard)
FRONTEND_URL=http://localhost:5173
```

A provider with an empty client ID/secret is not offered and its routes return 503.

`OAUTH_REDIRECT_URI` was removed. If it is still set, the backend **fails at startup** with a message telling you to set `OAUTH_REDIRECT_BASE_URL` instead and unset it.

In production, set `OAUTH_REDIRECT_BASE_URL=https://your-domain.com/api/v1/auth`, `FRONTEND_URL` to the frontend origin, and update every provider's registered redirect URI to match.

## Security

- **State**: generated per flow, stored hashed, one-time use, expiring, and bound to the provider name.
- **Linking**: the link target user is re-checked at callback against the signed session; logging out or switching accounts mid-flow cancels the link. A provider account already linked to another user is rejected.
- **Auto-linking**: only for Google/GitHub, and only when the provider reports the email verified.
- **Unlinking**: blocked if the user has no password and this is their only linked provider ("Cannot remove last authentication method").
- **IdP signups**: `is_verified` and `email_verified_at` are set from the provider's email-verified flag.
- Provider access/refresh tokens are not persisted.

## Troubleshooting

- **"Provider ... not configured" (503)** — client ID/secret missing; restart after editing `.env`.
- **"Invalid state token" / "State token expired"** — restart the flow; don't refresh the callback page.
- **"Create and verify an account first, then link Microsoft in Settings"** — expected; sign in another way and link Microsoft from Settings.
- **"Email not verified by provider. Cannot auto-link account."** — the email belongs to an existing account and the provider is Microsoft or didn't verify it; sign in with the existing method, then link from Settings.
- **Redirect URI mismatch** — `OAUTH_REDIRECT_BASE_URL` must exactly match what each provider has registered (scheme included, no trailing slash).
