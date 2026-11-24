# Operations Runbook

## Where things live

| Deployment | Database | Logs | Restart |
|------------|----------|------|---------|
| Proxmox LXC | `/opt/recipe-catalog/backend/data/recipes.db` | `journalctl -u recipe-catalog-backend -f` | `sudo systemctl restart recipe-catalog-backend` |
| Docker | `/app/data/recipes.db` in the `sqlite_data` volume | `docker compose logs -f backend` (the in-container log file is on tmpfs) | `docker compose restart backend` |
| Local dev | `backend/recipes.db` | `backend/logs/app.log` and the terminal | restart `uv run uvicorn app.main:app --reload` |

Commands below use `recipes.db`; substitute the path for your deployment. For Docker, copy the file out first (see the [Docker guide](../docker/DOCKER-DEPLOYMENT.md#backups)).

## Database

### Migrations

```bash
cd backend
uv run alembic upgrade head     # apply pending migrations
uv run alembic downgrade -1     # roll back one
uv run alembic history
uv run alembic current
```

The backend refuses to start if the database is not at the Alembic head. Proxmox (`update-app.sh`) and Docker (the container entrypoint) migrate automatically on update.

### Backup and restore

Stop the backend before restoring.

```bash
sqlite3 recipes.db ".backup recipes-$(date +%Y%m%d).db"   # safe while running
cp recipes-YYYYMMDD.db recipes.db                          # restore
```

### Purge trashed recipes

Recipes are soft-deleted (`deleted_at` set) and stay in the user's trash until purged. Nothing purges them automatically; this is a manual step. Collections are hard-deleted immediately and need no purge.

```bash
sqlite3 recipes.db "DELETE FROM recipes WHERE deleted_at < datetime('now', '-30 days');"
```

### Optimize

```bash
sqlite3 recipes.db "VACUUM;"
```

### Reset (destructive, local dev)

```bash
cd backend
cp recipes.db recipes.db.backup
rm recipes.db
uv run alembic upgrade head
```

## Monitoring

```bash
curl http://localhost:8000/health   # Proxmox / local dev
curl http://localhost:8080/health   # Docker (proxied by the frontend)
```

## Data export/import (via API)

Requires an access token (`Authorization: Bearer`). Add `/api/v1/...` to your site's base URL.

```bash
# Export all of your recipes as JSON (also: format=markdown, format=text)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/export/recipes?format=json" > recipes.json

# Export everything (recipes, collections, preferences)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/export/all > export.json

# Import a schema.org Recipe JSON file (single object or array)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -F "file=@recipes.json" -F "duplicate_handling=skip" \
  http://localhost:8000/api/v1/import/recipes
```

`POST /api/v1/import/recipes/json` takes the same recipes as a JSON array request body instead of a file upload.

## Security scanning

```bash
cd backend && uvx pip-audit -r <(uv export --format requirements-txt --no-hashes --no-emit-project)
cd frontend && pnpm audit
```

Dependabot opens PRs for vulnerable dependencies (`.github/dependabot.yml`).

## Troubleshooting

**`pnpm dev` fails with `Invalid declaration: …` on a `?svelte&type=style&lang.css` module** (usually right after a dependency update): Vite's cache is stale. Stop the dev server, run `rm -rf frontend/node_modules/.vite`, restart, and hard-refresh the browser tab.
