# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Frontend (`cd frontend` first)

```bash
pnpm dev          # dev server on :5173
pnpm build        # production build
pnpm check        # svelte-check type checking
pnpm lint         # ESLint
pnpm format       # Prettier
pnpm test         # Vitest (single run)
pnpm test:watch   # Vitest (watch mode)
```

Run a single test file: `pnpm test src/lib/components/RecipeCard.test.ts`

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

## Architecture

### Monorepo layout

```
frontend/   SvelteKit app (pnpm workspace)
backend/    FastAPI app (uv-managed)
database/   schema.sql + seed.sql
```

The frontend proxies `/api/*` requests to the backend at `:8000` (configured in `frontend/vite.config.ts`).

### Frontend

**Routing**: SvelteKit file-based. `+page.svelte` = page, `+layout.svelte` = layout wrapper, `[id]/` = dynamic segment.

**Root layout** (`src/routes/+layout.svelte`): Renders `<Navbar>` for authenticated users on non-auth pages. Auth pages (`/` and `/auth/*`) get no navbar. Global `<ConfirmDialog>` and `<Toast>` are mounted here.

**State**: Two Svelte stores drive shared state:
- `src/lib/stores/auth.ts` — user session, login/logout, JWT token
- `src/lib/stores/collections.ts` — collection list and CRUD

**API client**: `src/lib/api/client.ts` is the base fetch wrapper (attaches auth headers). Resource modules (`recipes.ts`, `collections.ts`, etc.) build on top of it.

**Styling**: Tailwind CSS v4. Global styles and theme definitions live in `src/app.css`. Config in `tailwind.config.js` (loaded via `@config` directive in the CSS file — required for v4). Plugins declared with `@plugin` in the CSS, not in the JS config.

**Theme system**: Four themes (`garden-fresh`, `bistro`, `dark`, `high-contrast`) defined as CSS custom property blocks under `[data-theme="..."]` selectors in `app.css`. Applied by setting `data-theme` on `<html>`. Use `var(--primary-*)`, `var(--accent-*)`, `var(--neutral-*)`, `var(--text-*)`, `var(--radius-*)` — do not hardcode colors.

**Tailwind v4 gotchas**: Do not add names like `sm/md/lg/xl/2xl/3xl` to `theme.extend.spacing` or `theme.extend.borderRadius` — they shadow Tailwind's built-in `max-w-*`, `rounded-*`, etc. utilities. Keep custom sizing in CSS variables only.

**Testing**: Vitest + jsdom + `@testing-library/svelte`. The `svelteTesting()` plugin in `vite.config.ts` is required for Svelte 5 browser bundle resolution — without it, `mount()` resolves to the SSR bundle and tests fail.

### Backend

**Entry point**: `backend/app/main.py` (registered as `app.main:app`).

**Layer separation**:
- `app/api/` — route handlers (thin, delegate to services or direct DB calls)
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic v2 request/response schemas (separate from models)
- `app/core/` — config, database session, security utilities, FastAPI dependencies
- `app/services/` — business logic

**Key dependencies** (injected via FastAPI's `Depends`):
- `get_db()` — async database session
- `get_current_user()` / `get_current_active_user()` — JWT auth

**API versioning**: All endpoints are under `/api/v1/`. Legacy `/api/*` paths redirect with deprecation warnings.

**Database**: SQLite locally (`backend/recipes.db`), Cloudflare D1 in production. Async access via `aiosqlite` + SQLAlchemy async. Migrations managed by Alembic in `backend/alembic/`.

**Soft delete**: Recipes and collections have a `deleted_at` field. Records are kept 30 days before permanent deletion. Most queries must filter `WHERE deleted_at IS NULL`.

**Auth**: JWT (PyJWT) + Argon2 password hashing. OAuth via Authlib (Google, Microsoft, GitHub). Email verification and password reset use time-limited tokens stored in the DB.
