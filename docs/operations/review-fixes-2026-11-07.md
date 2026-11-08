# November 7, 2026 review fixes

This change addresses `findings-2026-11-07.md`. The original findings document remains a record of the review.

| Finding | Resolution |
| --- | --- |
| H1 | HTTP(S)-only bounded recipe URLs on writes/imports; unsafe legacy links become absent in responses; frontend link parsing is defensive and external links have `noopener noreferrer`. |
| H2 | Microsoft email and `preferred_username` cannot establish email ownership. Microsoft accounts must be linked from an existing verified account through browser-bound OAuth state. Pending links are invalidated on login/logout/account switches. |
| H3–H4 | SQLite token expiry uses the shared UTC helper; Authlib has signed browser sessions and its normal state validation. OAuth callbacks preserve cookies and redirect browser navigations. |
| H5 | Duplicates inherit household scope. The forward migration also repairs existing orphaned recipe scope. |
| H6 | Extreme ingredient quantities, recursion, invalid numeric times, and duration overflow are handled without crashing writes. Non-finite times are cleared. |
| H7 | JSON imports are module-level. AI failures have distinct HTTP/timeout/connection/JSON/shape/unexpected log events with tracebacks, operation, model, exception type, and applicable status/request ID/parse-position context. Client errors exclude upstream bodies and private inputs. |
| H8–H9 | Imports handle existing duplicate names deterministically and batch lookups. Invalid entries fail individually. Imports cap recipes at 500, images at five, and embedded image data at the configured image size. |
| I1 | A frozen pre-001 baseline supports empty databases; the duplicate historical email column revision is a no-op. Forward migrations reconcile schema origins. |
| I2 | LXC defaults to production and requires HTTPS; local HTTP requires an explicit development option. |
| I3 | uv is pinned to 0.13.7 in Docker and checksum-verified on LXC. Node installation uses a signed apt repository instead of executing a downloaded setup script. |

The medium and low findings are addressed in the corresponding areas:

- Authentication: SQL token invalidation predicates, session revocation on password changes/reset/reuse, uniform recovery responses, normalized email lookups, bounded passwords, safe redirects/JWT subjects, and passwordless-account handling. Remote failed passwords no longer globally lock an account; login remains rate limited per client IP. Refresh sends the CSRF header. Public recovery endpoints use one-time capabilities rather than requiring an existing login cookie, and recovery pages use versioned API client paths.
- Email changes: the current password is required; the old account address remains active until the new address is verified.
- Households: secure five-word invite codes, normalized collision checks, owner-only generation, lookup/join rate limits, escaped email HTML, hashed invitation secrets, and non-expired invitation lookup. Departing members receive a usable personal household. Recipes, collections, shopping lists, and individually owned planned meals follow their owners; joining merges weeks without losing meal authorship. Deleting a household with other members is refused.
- Recipe correctness: trashed recipes cannot be edited, collected, or used to generate lists. Only owners may directly read their own trashed recipes. Collection IDs are deduplicated; collection mutations and imports use bulk lookups. Shopping lists use parsed ingredients, skip headers, and bulk-fetch household-scoped active recipes.
- AI: bounded inputs and catalog queries, selected catalog IDs honored before limiting, validated model responses, and unknown recipe IDs cleared. API handlers preserve classified service errors rather than replacing or logging them a second time.
- Export: mixed category/cuisine types, string ingredients, nested instruction sections, and Unicode fonts are handled. PDF conversion skips unused remote image fetches and renders in a worker thread.
- Frontend: cookie-only OAuth completion, refresh on initialization and exports, one retry path, refresh generation tracking, safe login redirects, sequenced search/detail requests, shared delayed download cleanup, and an application-wide system-theme listener.
- Infrastructure: unprivileged runtime containers, frozen installs, database migrations before startup, existing-volume ownership initialization, upload limits/security headers, correct health URLs, private backups/logs, quoted branch arguments, a single SQLite worker, Node 24 builds, Docker Dependabot, and CI. Static bootstrap scripts are externalized so the strict script CSP permits application startup. Both installation and update scripts restore nginx-readable static paths.
- Tooling/docs: coverage supports greenlet/thread concurrency, asyncio fixture scope is explicit, and concurrency tests use separate request sessions against a file database. `CLAUDE.md` correctly describes hard-deleted collections.

## Deployment and rollback

Apply the migrations before starting an updated backend:

```sh
cd backend
uv run alembic upgrade head
```

Docker performs this automatically. Its one-shot `data-permissions` service also updates existing SQLite volume ownership before the unprivileged backend starts. LXC requires `--domain <hostname>` for production HTTPS; use `--development` only for local HTTP.

The household integrity migration repairs legacy ownership scope, creates personal memberships for users previously left without one, and preserves planned-meal entries across colliding weeks. It removes collection associations that would span households after repair. Historical meal authorship is backfilled from the original weekly plan creator because older releases did not record individual authors.

The `20261107_drop_legacy_ms_links` migration **deletes every existing Microsoft identity-provider link**. Older releases auto-linked Microsoft accounts by an unverified email claim, and those rows cannot be told apart from legitimate links, so all are dropped. Affected users sign in with their password (or, for Microsoft-only accounts, use "forgot password" to their account email) and re-link Microsoft from Settings. Microsoft sign-up stays disabled. The deletion is not reversible by downgrade.

Login is throttled per account as well as per IP: 10 failed attempts per email within a sliding 15-minute window return 429. The counter lives in process memory (one backend worker) and is never a persistent lockout; the `users.failed_login_attempts`/`locked_until` columns are unused. Reuse of a refresh token rotated within the last 30 seconds is treated as a concurrent-request race and only rejected; later reuse still revokes all of the user's sessions. Changing the password signs out every other session and re-issues cookies for the current one.

Invitation secrets are hashed in place without changing existing emailed links. A downgrade cannot reconstruct plaintext secrets: pending invitations must be reissued after rolling back to a plaintext-token release. Take a database backup before deploying migrations.

## Verification

Regression coverage includes URL injection, SQLite expiry, Microsoft linking, token invalidation/session revocation, email changes, public recovery with CSRF enabled, household departure/join/departure, foreign-key-enforced household deletion, legacy data migration, import limits, invalid AI responses, classified AI diagnostics, Unicode export, chunked upload limits, safe redirects, delayed refresh responses, and blob-export recovery.

The migration suite verifies empty-database upgrade, schema parity, full downgrade/re-upgrade, and an existing-data upgrade with orphaned recipes and colliding meal-plan weeks. Local validation also includes lint, type checks, frontend build/tests, dependency audit, shell syntax, and Compose configuration.

Docker image execution, browser visual inspection, and real-provider OAuth/SMTP verification remain environment checks: the local Docker daemon and browser host were unavailable, and external provider credentials were not used. Existing frontend lint warnings and one low-severity dependency advisory remain; no lint errors or high-severity audit findings are accepted.
