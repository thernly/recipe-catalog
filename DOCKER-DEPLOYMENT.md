# Recipe Catalog - Docker Deployment Guide

This guide explains how to run the Recipe Catalog application using Docker and Docker Compose. It creates two containers:

1. `backend` – FastAPI application (Python 3.13, uv, SQLite)
2. `frontend` – Nginx serving the built SvelteKit static files and reverse-proxying `/api` to the backend

SQLite data is persisted in a named volume.

---

## 1. Prerequisites

- Docker Engine 24+ and Docker Compose plugin (`docker compose version`) installed
- Clone of repository (`git clone <repo> && cd recipe-catalog`)
- (Optional) Domain name + reverse proxy / TLS termination (Traefik / Caddy / Nginx external)

---

## 2. Directory & Files Added

| Path | Purpose |
|------|---------|
| `backend/Dockerfile` | Builds backend image using uv and Python 3.13 |
| `backend/.dockerignore` | Excludes unnecessary files from backend build context |
| `frontend/Dockerfile` | Builds frontend static assets using adapter-static, serves via nginx |
| `frontend/.dockerignore` | Excludes unnecessary files from frontend build context |
| `docker/nginx.conf` | Nginx config for SPA + API proxy |
| `docker-compose.yml` | Orchestrates services + volume + healthcheck |
| `DOCKER-DEPLOYMENT.md` | This guide |

---

## 3. Backend Environment

Create `backend/.env` (do NOT commit secrets):

```env
DATABASE_URL=sqlite+aiosqlite:///./data/recipes.db
SECRET_KEY=<generate-with: openssl rand -hex 32>
# Comma-separated list (no brackets)
ALLOWED_ORIGINS=http://localhost:8080
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@recipecatalog.app
FROM_NAME=Recipe Catalog
APP_NAME=Recipe Catalog
FRONTEND_URL=http://localhost:8080
RATE_LIMIT_PER_MINUTE=60
```

---

## 4. Build & Run

```bash
# Build images
docker compose build

# Start services (detached)
docker compose up -d

# View logs (combined)
docker compose logs -f
```

Access:

- Frontend: <http://localhost:8080>
- Backend API (proxied through frontend): <http://localhost:8080/api/docs>

**Note**: The backend port (8000) is not exposed publicly for security. Access the API through the frontend proxy at port 8080.

---

## 5. Development Workflow (Optional)

For active development you may want live reload. Suggested adjustments:

1. Mount backend source into container:

   ```yaml
   backend:
     volumes:
       - ./backend:/app
       - sqlite_data:/app/data
   ```

2. Install dev dependencies: remove `--no-dev` logic in Dockerfile or run interactively.
3. Run with `--reload`:

   ```yaml
   command: ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
   ```

4. Frontend: Instead of nginx build stage, run dev server separately:
   - Comment out frontend service in compose
   - Run locally: `cd frontend && pnpm dev --host`

---

## 6. Production Considerations

| Aspect | Recommendation |
|--------|---------------|
| Secrets | Use Docker secrets or env vars injected by orchestrator |
| TLS | Terminate at external reverse proxy (Caddy, Traefik, Nginx) |
| Scaling | Stateless frontend; backend can scale horizontally (move to Postgres for multi-instance) |
| Persistence | Named volume `sqlite_data`; backup regularly |
| Healthcheck | Add `healthcheck:` for backend hitting `/api/recipes` or `/api/docs` |
| Logs | Aggregate via `docker logs` or ship to external system |

### Sample Healthcheck

The backend service includes a Python-based healthcheck (no curl required):

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/docs').read()"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 10s
```

---

## 7. Updating

```bash
docker compose pull        # if switching to remote registry images
docker compose build       # rebuild after code changes
docker compose up -d       # recreate containers
```

Database migrations (after code update):

```bash
docker compose exec backend uv run alembic upgrade head
```

---

## 8. Backups

SQLite file path inside volume: `/app/data/recipes.db`.

Backup command:

```bash
# Create a temporary container to copy out the DB
DB_CONTAINER=$(docker compose ps -q backend)
docker cp "$DB_CONTAINER:/app/data/recipes.db" "recipes-$(date +%Y%m%d-%H%M%S).db"
```

Restore (container stopped):

```bash
docker cp recipes-yyyyMMdd-HHMMSS.db "$DB_CONTAINER:/app/data/recipes.db"
```

---

## 9. Switching to Postgres (Optional Future)

1. Add service:

```yaml
postgres:
  image: postgres:16-alpine
  environment:
    - POSTGRES_DB=recipes
    - POSTGRES_USER=recipe
    - POSTGRES_PASSWORD=change_me
  volumes:
    - pg_data:/var/lib/postgresql/data
  restart: unless-stopped
```

2. Update backend env:

```bash
DATABASE_URL=postgresql+asyncpg://recipe:change_me@postgres:5432/recipes
```

3. Run migrations: `docker compose exec backend uv run alembic upgrade head`

---

## 10. Stopping & Removing

```bash
docker compose down            # stop & remove containers
docker compose down -v         # also remove volumes (DATA LOSS!)
```

---

## 11. Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| 502 Bad Gateway | Backend not reachable | `docker compose logs backend` / healthcheck failing |
| API CORS errors | ALLOWED_ORIGINS mismatch | Update `ALLOWED_ORIGINS` in `.env` (comma-separated, no brackets) |
| Email failures | SMTP misconfig | Check env & backend logs |
| DB locked | Concurrent writes in SQLite | Consider Postgres for multi-user high write load |
| Static not updating | Old image cached | `docker compose build --no-cache` |
| SvelteKit build fails | Missing adapter-static | Ensure `@sveltejs/adapter-static` is in package.json devDependencies |

Inspect running containers:

```bash
docker compose ps
docker compose logs -f backend
docker compose exec backend bash
```

---

## 12. Automatic Restart

Containers use `restart: unless-stopped`; they will restart after daemon or host reboot. Verify with:

```bash
docker compose ps
```

---

## 13. Security Notes

- Replace default `SECRET_KEY` immediately
- Do not expose backend port publicly unless needed (remove `8000:8000` mapping)
- Run Docker Engine with regular updates
- Consider scanning images (`docker scout cves backend`)

---

## 14. Quick Start Summary

```bash
git clone <repo>
cd recipe-catalog
cp backend/.env.example backend/.env   # create and edit secrets
# (Edit backend/.env)
docker compose build
docker compose up -d
docker compose logs -f
```

Access at: `http://localhost:8080`

---
**Guide Version**: 1.1
**Last Updated**: 2025-11-24

**Changelog**:
- v1.1 (2025-11-24): Fixed Dockerfile COPY paths, added .dockerignore files, configured adapter-static, added Python-based healthcheck, removed direct backend port exposure, clarified ALLOWED_ORIGINS format
- v1.0 (2025-11-23): Initial version
