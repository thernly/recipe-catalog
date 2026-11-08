# Docker Deployment

`docker-compose.yml` runs three services:

| Service | What it does |
|---------|--------------|
| `data-permissions` | One-shot init container: `chown`s the `sqlite_data` volume to UID 10001 so the non-root backend can write to it, then exits |
| `backend` | FastAPI on Python 3.13 (`backend/Dockerfile`). Runs `alembic upgrade head` on every start (`backend/docker-entrypoint.sh`), then uvicorn on port 8000. Port 8000 is only exposed on the internal network, not published to the host |
| `frontend` | nginx (`frontend/Dockerfile`, `docker/nginx.conf`) serving the static SvelteKit build and proxying `/api` and `/health` to the backend. Published on `:8080` |

The database is `/app/data/recipes.db` inside the `sqlite_data` named volume.

## Prerequisites

Docker Engine with the Compose plugin (`docker compose version`).

## Configure

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`. The settings that matter here:

| Variable | Notes |
|----------|-------|
| `SECRET_KEY` | Required, at least 32 characters: `openssl rand -hex 32` |
| `ENVIRONMENT` | `production` (the image default) |
| `ALLOWED_ORIGINS` | Comma-separated, no brackets. Include the URL users browse to, e.g. `http://localhost:8080` |
| `FRONTEND_URL` | Used in email links, e.g. `http://localhost:8080` |
| `SMTP_*`, `FROM_EMAIL` | Needed for verification and password-reset emails |
| `OAUTH_REDIRECT_BASE_URL`, `*_CLIENT_ID/SECRET` | Optional OAuth providers |
| `OPENROUTER_API_KEY` | Optional AI features |

Compose sets these itself, overriding `.env`:

- `DATABASE_URL` is forced to `sqlite+aiosqlite:///./data/recipes.db` (the volume).
- `COOKIE_SECURE=false`, because the stack serves plain HTTP on `:8080` and browsers drop `Secure` cookies over HTTP, which makes login silently fail. Remove this line from `docker-compose.yml` once you serve over HTTPS.
- `APP_VERSION` is passed through from your shell. The build context has no git history, so set it when building:

```bash
APP_VERSION=$(scripts/app-version.sh) docker compose up -d --build
```

## Run

```bash
APP_VERSION=$(scripts/app-version.sh) docker compose up -d --build
docker compose logs -f
```

Open <http://localhost:8080>. Migrations run automatically; there is no `uv` in the runtime image, so don't try `docker compose exec backend uv run ...`.

The interactive API docs (`/docs`, `/redoc`) are only served when `DEBUG=true`, and nginx does not proxy them (they are not under `/api`).

## Update

```bash
git pull
APP_VERSION=$(scripts/app-version.sh) docker compose up -d --build
```

The backend applies new migrations when it restarts.

## Health checks

- Backend: Python `urllib` request to `http://localhost:8000/health` inside the container.
- Frontend: `wget` to `http://127.0.0.1:8080/health`, which nginx proxies to the backend.

The frontend waits for the backend to be healthy before starting. `docker compose ps` shows the status. Both services use `restart: unless-stopped`.

## Hardening

Both long-running containers run with `read_only: true`, `cap_drop: [ALL]` and `no-new-privileges`. The writable paths are tmpfs mounts (backend `/tmp` and `/app/logs`, frontend `/tmp`, `/var/cache/nginx`, `/var/run`) plus the data volume. Because `/app/logs` is tmpfs, the backend's log file is lost on restart; use `docker compose logs`.

The `app` network has a fixed subnet, `172.30.0.0/24`: backend `172.30.0.2`, frontend `172.30.0.3`. The backend trusts `X-Forwarded-*` headers only from `172.30.0.3` (`--forwarded-allow-ips` in `backend/Dockerfile`), which the rate limiter relies on for client IPs. If you change the frontend's address, change that flag too.

## TLS / reverse proxy

Terminate TLS in front of the stack and proxy everything to `:8080`:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    # ssl_certificate ... (e.g. from certbot --nginx)

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Once served over HTTPS, remove `COOKIE_SECURE=false` from `docker-compose.yml` and update `ALLOWED_ORIGINS` and `FRONTEND_URL` to the HTTPS URL.

## Backups

```bash
docker compose cp backend:/app/data/recipes.db "recipes-$(date +%Y%m%d-%H%M%S).db"
```

Restore with the backend stopped:

```bash
docker compose stop backend
docker compose cp recipes-YYYYMMDD-HHMMSS.db backend:/app/data/recipes.db
docker compose start backend
```

SQLite is single-writer: run one backend instance, not several.

## Stop and remove

```bash
docker compose down        # stop and remove containers
docker compose down -v     # also delete the sqlite_data volume (DATA LOSS)
```

## Troubleshooting

| Symptom | Check |
|---------|-------|
| 502 Bad Gateway | `docker compose logs backend`; a failed migration or bad `.env` stops the backend from starting |
| Login appears to succeed but you're logged out | `COOKIE_SECURE` is true while serving over HTTP |
| CORS errors | `ALLOWED_ORIGINS` must include the exact origin users browse to |
| Backend can't write the database | The `data-permissions` service must complete; check `docker compose logs data-permissions` |
| Stale frontend after changes | `docker compose build --no-cache frontend` |

Shell into a container with `docker compose exec backend sh` (the Alpine-based frontend image has no `bash`).
