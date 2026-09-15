# Recipe Catalog - AI Agent Guidelines

See **CLAUDE.md** for commands, architecture, project structure, and tech stack. This file adds agent-specific behavioral guidance on top of that foundation.

## Working in This Codebase

- Read relevant files before making changes — don't assume structure from filenames alone.
- When a change touches the API, check both the backend route handler and the frontend `src/lib/api/` client module.
- UI changes must use theme CSS variables (e.g. `var(--primary-500)`) — never hardcode colors. There are four theme blocks (`garden-fresh`, `bistro`, `dark`, `high-contrast`), so check your change against a light, a dark, and the high-contrast palette.
- New pages automatically inherit the navbar via the root layout for authenticated users. No wiring needed unless the page is under `/auth/` or is the landing page `/`.
- Never call `fetch` directly from a component or page — go through `apiRequest` in `src/lib/api/client.ts`. It attaches the CSRF token and handles the 401 → refresh → retry flow; a raw `fetch` silently skips both.
- Reuse the shared UI primitives rather than rolling new ones: the `dialog` and `toast` stores drive the globally mounted `ConfirmDialog`/`Toast`, and page sizes, debounce delays, and timeouts live in `src/lib/constants.ts`.

## Adding Common Things

**New API endpoint**: schema in `app/schemas/` → model in `app/models/` if needed → handler in `app/api/` → **register the router in `app/api/v1/__init__.py`** (a new module is unreachable until it is included there) → update frontend `src/lib/api/` client → tests in `backend/tests/`.

**New page**: create `src/routes/<path>/+page.svelte`. Navbar is automatic for non-auth pages when the user is logged in. There is no shared route guard — `src/routes/dashboard/+page.svelte` is the only page that redirects unauthenticated visitors (`onMount` → `auth.subscribe` → `goto('/auth/login')`); every other private page relies on the API client turning a failed refresh into a logout. Copy the dashboard pattern if the page must not render without a user.

**Database schema change**: update the SQLAlchemy model → export it from `app/models/__init__.py` (metadata only sees imported models) → update the Pydantic schema → `uv run alembic revision --autogenerate -m "..."` → **review the generated migration before applying it** → `uv run alembic upgrade head` (the app refuses to start while the DB revision trails the Alembic head) → verify the migration runs both up and down.

> Autogenerate only sees what is on `Base.metadata`. If a migration adds a composite index, declare it in the model's `__table_args__` too — otherwise the next autogenerate proposes dropping it.

## Constraints

- No analytics, tracking, or third-party data collection — ever.
- All backend I/O must be async.
- **Household scoping**: reads and lists scope by household (`Depends(get_user_household)` → `WHERE household_id == household.id`); mutations, deletes, and trash views scope by owner (`WHERE user_id == current_user.id`). Using the wrong one either leaks another member's data or hides shared recipes.
- Soft-delete pattern: recipes and collections have `deleted_at`; always filter `WHERE deleted_at IS NULL` in queries unless intentionally accessing trash.
- API endpoints are versioned under `/api/v1/` — do not add unversioned routes.
- Raise `AppException` subclasses from `app/core/exceptions.py` instead of hand-building error responses; the global handlers produce the `{error_code, message, details, correlation_id}` envelope the frontend's `ApiError` expects.
- Log through structlog with an event name first (`logger.info("recipe_created", recipe_id=id)`) — not f-strings.
