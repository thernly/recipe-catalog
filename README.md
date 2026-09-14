# Recipe Catalog App

A privacy-focused web application for organizing and managing your personal recipe collection.

**Privacy First**: No tracking, no analytics, no third-party data sharing. Your recipes are yours.

## Features

- **Recipe Management** — Full CRUD with search, filtering, and pagination
- **Collections** — Organize recipes into custom collections with emoji icons
- **Import/Export** — JSON import; bulk export as JSON, Markdown, or plain text. Single recipes also export as PDF
- **Meal Planning** — Weekly calendar view with shopping list generation
- **Shopping Lists** — Generate from recipes or meal plans
- **AI Features** — Recipe generation from ingredients and multi-day menu suggestions (via OpenRouter)
- **Multi-User Households** — Share recipes with family members via email invitations or shareable join links
- **OAuth Sign-In** — Google, Microsoft, and GitHub
- **Account Security** — Refresh-token sessions, plus lockout after 5 failed logins for 15 minutes
- **Personalization** — Dietary preferences, custom cuisines, and custom categories
- **Themes** — Garden Fresh (default), Bistro, Dark, and High Contrast, plus System to follow your device preference
- **Soft Delete** — Deleted recipes and collections are retained for recovery; purging is a manual operator step (see the [runbook](docs/operations/runbook.md))

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | SvelteKit, Svelte 5, TypeScript, Tailwind CSS v4 |
| Backend | FastAPI, Python 3.13, SQLAlchemy (async), Alembic |
| Database | SQLite locally, Cloudflare D1 in production |
| Auth | JWT + Argon2, OAuth via Authlib |
| Deployment | Cloudflare Pages + Workers, or self-hosted Docker |

## Quick Start

### Prerequisites

- Node.js 22.12+, pnpm
- Python 3.13+, [uv](https://astral.sh/uv)

### Frontend

```bash
cd frontend
pnpm install
echo "VITE_API_URL=http://localhost:8000" > .env
pnpm dev
```

Runs on `http://localhost:5173`.

### Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Runs on `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

Create `backend/.env`:

```env
DATABASE_URL=sqlite+aiosqlite:///./recipes.db
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
ALGORITHM=HS256
# Access tokens are deliberately short-lived; refresh tokens cover session length.
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
DEBUG=True
ENVIRONMENT=development

# Optional: email (for verification and password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Recipe Catalog
FRONTEND_URL=http://localhost:5173

# Optional: OAuth providers
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
OAUTH_REDIRECT_BASE_URL=http://localhost:8000/api/v1/auth

# Optional: AI features (openrouter.ai)
OPENROUTER_API_KEY=
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

### Load sample data (optional)

```bash
sqlite3 backend/recipes.db < database/seed.sql
```

## API

All endpoints are under `/api/v1/`. Interactive docs at `http://localhost:8000/docs`.

## Operations

- [Deployment guide](docs/operations/deployment.md) — Cloudflare and Docker deployment
- [Runbook](docs/operations/runbook.md) — database backups, migrations, monitoring, troubleshooting

## License

MIT
