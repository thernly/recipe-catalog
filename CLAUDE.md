# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

`AGENTS.md` sits alongside this file with behavioral guidance (how to add an endpoint/page/migration, project constraints). This file covers commands and architecture.

## Commands

### Frontend (`cd frontend` first)

```bash
pnpm dev          # dev server on :5173
pnpm build        # production build
pnpm check        # svelte-kit sync + svelte-check type checking
pnpm lint         # ESLint
pnpm format       # Prettier
pnpm test         # Vitest (single run)
pnpm test:watch   # Vitest (watch mode)
```

Run a single test file: `pnpm test src/lib/components/RecipeCard.test.ts`

`frontend/` is its own pnpm workspace root (`frontend/pnpm-workspace.yaml`, `frontend/pnpm-lock.yaml`) — there is no root-level `package.json`. Always install and run from inside `frontend/`.

### Backend (`cd backend` first)

```bash
uv run uvicorn app.main:app --reload   # dev server on :8000
uv run pytest                          # all tests
uv run pytest tests/test_auth.py       # single file
uv run pytest tests/test_auth.py::test_register_user  # single test
uv run pytest --cov=app --cov-report=term-missing     # with coverage
uv run ruff check .                    # lint
uv run ruff format .                   # format
uv run mypy app/                       # type check
uv run alembic upgrade head            # apply migrations
uv run alembic revision --autogenerate -m "description"  # new migration
```

Always use `uv run` — never `pip install` or bare `python`.

The app **will not start** against an out-of-date database: `init_db()` reads `alembic_version` and raises unless it matches the Alembic head. It deliberately does not create tables from model metadata (that would leave the DB unstamped and break later upgrades). After pulling migrations, run `uv run alembic upgrade head`.

There is no CI workflow in `.github/` (only Dependabot) — run lint, type check, and tests locally before committing.

## Architecture

### Monorepo layout

```
frontend/   SvelteKit app (pnpm)
backend/    FastAPI app (uv-managed)
database/   schema.sql + seed.sql
docker/     nginx.conf for the containerized frontend
scripts/    Proxmox LXC deploy helpers
docs/       features/, operations/ (deployment.md, runbook.md), requirements/
```

The frontend proxies `/api/*` to the backend at `:8000` (`frontend/vite.config.ts`). In dev, `API_BASE_URL` is empty so requests stay relative and hit that proxy; in production it falls back to `location.origin`. All calls go through `API_V1_URL` (`src/lib/config.ts`).

### Household scoping — the central data-access rule

Every user belongs to exactly one household (created at registration via `app/services/household.py`). Recipes, collections, meal plans, and shopping lists all carry both `user_id` (owner) and `household_id` (sharing scope), and the split matters:

- **Reads/lists** scope by household: `Depends(get_user_household)`, then `WHERE household_id == household.id`.
- **Mutations and deletes** scope by owner: `WHERE user_id == current_user.id`.
- **Trash views** scope by owner too: `Recipe.user_id == current_user.id, Recipe.deleted_at.isnot(None)`.

Getting this wrong either leaks other members' data or hides shared recipes. Mirror the existing query in `app/api/recipes/search.py` and `app/api/collections.py`.

### Recipe storage model

A recipe's content lives in a single `recipe_data` JSON column in **schema.org/Recipe format, camelCase** (`recipeIngredient`, `recipeInstructions`) — deliberately not snake_case, so import/export round-trips with the standard. `name`, `cuisine`, `category`, and `total_time_minutes` are denormalized into indexed columns for search and filtering; when writing recipe data, update both the JSON and the denormalized columns.

### Backend

**Entry point**: `backend/app/main.py` (`app.main:app`). It wires middleware, exception handlers, `/` and `/health`, and includes `api_v1_router`.

**Layer separation**:
- `app/api/` — route handlers (thin; `recipes/` is split into `crud.py`, `search.py`, `export.py`)
- `app/api/v1/__init__.py` — the single `APIRouter(prefix="/api/v1")` where every router is registered with its prefix and tag
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic v2 request/response schemas (separate from models)
- `app/core/` — config, database session, security, deps, email, OAuth, structured logging, exceptions
- `app/services/` — business logic (`ai.py`, `household.py`, `recipe_export.py`)
- `app/middleware/` — CSRF, correlation ID
- `app/utils/` — file validation, PDF export, recipe formatting

**Dependencies** (`app/core/deps.py`, injected via `Depends`): `get_db()`, `get_current_user()`, `get_current_verified_user()`, `get_optional_current_user()`, `get_user_household()`. There is no `get_current_active_user` — the active check is inside `get_current_user`.

**API versioning**: everything is under `/api/v1/`. Unversioned legacy routes were removed; do not add them back (a few `/api/auth/*` strings survive only in the CSRF exempt list for tests).

**Auth is cookie-based**: login sets httpOnly `access_token` + `refresh_token` cookies plus a readable `csrf_token`. `get_current_user` accepts an `Authorization: Bearer` header first (used by tests and API clients) and falls back to the cookie. JWT via PyJWT, Argon2 hashing, OAuth via Authlib (Google/Microsoft/GitHub). Email verification and password reset use time-limited DB-stored tokens; refresh tokens are rows in `refresh_tokens`.

**CSRF**: double-submit cookie. State-changing methods (POST/PUT/PATCH/DELETE) must send `X-CSRF-Token` matching the `csrf_token` cookie. `CSRF_EXEMPT_PATHS` in `app/middleware/csrf.py` covers login/register/logout/OAuth; the whole check is skipped when `ENVIRONMENT == "testing"`.

**Error envelope**: every handler path (HTTPException, `AppException`, validation, unhandled) returns `{"error_code", "message", "details", "correlation_id"}`. Raise `AppException` subclasses from `app/core/exceptions.py` rather than shaping responses by hand; the frontend's `ApiError` reads `error_code`/`details`.

**Cross-cutting middleware** in `main.py`: rate limiting (slowapi, keyed on remote address), GZip, correlation ID (`X-Correlation-ID`, threaded into structlog context), security headers with a strict production CSP and a relaxed dev CSP, and a `Content-Length` guard at `MAX_UPLOAD_SIZE_MB`.

**Logging**: structlog with event-name-first calls (`logger.info("startup_cleanup_success", deleted_count=n)`) — keep that style, not f-strings.

`--autogenerate` only sees models registered on `Base.metadata`, which is why `alembic/env.py` imports `app.models`. A new model must be exported from `app/models/__init__.py`, and a composite index added by a migration must also be declared in the model's `__table_args__` — otherwise the next autogenerate proposes dropping it. `tests/test_migrations.py::test_env_py_metadata_is_populated` guards the import.

**Database**: SQLite locally (`backend/recipes.db`), Cloudflare D1 in production. Async via `aiosqlite` + SQLAlchemy async; Alembic owns the schema. Use `app/models/_utils.py` (`utc_now`, `ensure_utc`, `is_expired`) for datetimes — SQLite returns naive values.

**Soft delete**: recipes and collections have `deleted_at`. Most queries must filter `WHERE deleted_at IS NULL`. Purging is a **manual operator step** (see `docs/operations/runbook.md`) — the startup `cleanup_expired_data()` only removes expired OAuth states, so nothing auto-deletes trashed records.

**Backend tests**: `tests/conftest.py` sets required env vars before importing app modules, forces `ENVIRONMENT = "testing"` (disabling rate limits and CSRF), and runs against in-memory SQLite with `Base.metadata.create_all` and a `get_db` override. Authenticate via the `test_user_headers` fixture (bearer token). `asyncio_mode = "auto"`, so `async def test_*` needs no marker.

### Frontend

**Routing**: SvelteKit file-based. `+page.svelte` = page, `+layout.svelte` = layout, `[id]/` = dynamic segment.

**Root layout** (`src/routes/+layout.svelte`): renders `<Navbar>` for authenticated users on non-auth pages; `/` and `/auth/*` get no navbar. Global `<ConfirmDialog>` and `<Toast>` mount here, driven by the `dialog` and `toast` stores — call those stores instead of adding per-page modals.

**State**: `src/lib/stores/` — `auth.ts` (user session; login/logout work by cookie, the store holds the `User` object, not a token), `collections.ts` (collection list + CRUD), `dialog.ts`, `toast.ts`.

**API client**: `src/lib/api/client.ts` wraps fetch — always `credentials: "include"`, attaches `X-CSRF-Token` on mutations, and on 401 (or 403 on a mutation) transparently calls `/auth/refresh` once, deduped through a shared `refreshPromise`, then retries. Failed refresh logs out. Resource modules (`recipes.ts`, `collections.ts`, `meal-plans.ts`, `shopping-lists.ts`, `households.ts`, `ai.ts`, `users.ts`, `oauth.ts`) build on `apiRequest`; never call `fetch` directly from components.

**Constants**: page size, timeouts, debounce, toast duration, and `FETCH_CREDENTIALS` live in `src/lib/constants.ts` — reuse them rather than inlining numbers.

**Styling**: Tailwind CSS v4. Global styles and theme blocks in `src/app.css`; `tailwind.config.js` is loaded via `@config` in the CSS (required for v4) and plugins are declared with `@plugin`, not in the JS config.

**Theme system**: theme token blocks under `[data-theme="..."]` in `app.css` — `garden-fresh` (default, aliased by `light`/`classic`), `bistro` (aliased by `professional`), `dark`, `high-contrast`. `ThemeSwitcher.svelte` also offers `system`, which is not a CSS block: it resolves to `garden-fresh`/`dark` via `prefers-color-scheme` and listens for changes. Applied by setting `data-theme` on `<html>`. Use `var(--primary-*)`, `var(--accent-*)`, `var(--neutral-*)`, `var(--text-*)`, `var(--radius-*)` — do not hardcode colors.

**Tailwind v4 gotchas**: do not add names like `sm/md/lg/xl/2xl/3xl` to `theme.extend.spacing` or `theme.extend.borderRadius` — they shadow Tailwind's built-in `max-w-*`, `rounded-*` utilities. Keep custom sizing in CSS variables only.

**Testing**: Vitest + jsdom + `@testing-library/svelte`. The `svelteTesting()` plugin in `vite.config.ts` is required for Svelte 5 browser bundle resolution — without it, `mount()` resolves to the SSR bundle and tests fail.

**Deployment targets**: `@sveltejs/adapter-cloudflare` for Cloudflare Pages/Workers, `adapter-static` + `docker/nginx.conf` for the Docker image (`docker-compose.yml` serves the frontend on `:8080` and proxies to the backend).
