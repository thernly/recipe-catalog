# Recipe Catalog - AI Agent Guidelines

See **CLAUDE.md** for commands, architecture, project structure, and tech stack. This file adds agent-specific behavioral guidance on top of that foundation.

## Working in This Codebase

- Read relevant files before making changes — don't assume structure from filenames alone.
- When a change touches the API, check both the backend route handler and the frontend `src/lib/api/` client module.
- UI changes must use theme CSS variables (e.g. `var(--primary-500)`) — never hardcode colors. Test mentally against both light and dark themes.
- New pages automatically inherit the navbar via the root layout for authenticated users. No wiring needed unless the page is under `/auth/` or is the landing page `/`.

## Adding Common Things

**New API endpoint**: schema in `app/schemas/` → model in `app/models/` if needed → handler in `app/api/` → update frontend `src/lib/api/` client → tests in `backend/tests/`.

**New page**: create `src/routes/<path>/+page.svelte`. Add auth guard if private. Navbar is automatic for non-auth pages when user is logged in.

**Database schema change**: update SQLAlchemy model → update Pydantic schema → `uv run alembic revision --autogenerate -m "..."` → verify migration up and down.

## Constraints

- No analytics, tracking, or third-party data collection — ever.
- All backend I/O must be async.
- Soft-delete pattern: recipes and collections have `deleted_at`; always filter `WHERE deleted_at IS NULL` in queries unless intentionally accessing trash.
- API endpoints are versioned under `/api/v1/` — do not add unversioned routes.
