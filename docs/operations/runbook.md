# Operations Runbook

## Database

### Migrations

```bash
cd backend
uv run alembic upgrade head            # apply pending migrations
uv run alembic downgrade -1            # roll back one
uv run alembic history                 # view history
uv run alembic current                 # current revision
```

### Backup and restore (SQLite)

```bash
cd backend

# Backup
cp recipes.db recipes.db.backup-$(date +%Y%m%d)
# or:
sqlite3 recipes.db ".backup recipes.db.backup"

# Restore
cp recipes.db.backup recipes.db

# Dump to SQL
sqlite3 recipes.db .dump > backup.sql

# Restore from SQL
sqlite3 recipes.db < backup.sql
```

### Clean up soft-deleted records

Recipes and collections are soft-deleted (`deleted_at` timestamp set) and kept for 30 days before permanent deletion.

```bash
cd backend
sqlite3 recipes.db "DELETE FROM recipes WHERE deleted_at < datetime('now', '-30 days');"
sqlite3 recipes.db "DELETE FROM collections WHERE deleted_at < datetime('now', '-30 days');"
```

### Optimize database

```bash
sqlite3 recipes.db "VACUUM;"
```

### Reset database (destructive)

```bash
cd backend
cp recipes.db recipes.db.backup   # backup first
rm recipes.db
uv run alembic upgrade head
```

---

## Monitoring

### Health check

```bash
curl http://localhost:8000/health
```

### Application logs

```bash
cd backend
tail -f logs/app.log
grep ERROR logs/app.log
tail -n 100 logs/app.log
```

### Database size

```bash
ls -lh backend/recipes.db
```

---

## Troubleshooting

### Restart services

```bash
# Backend
pkill -f "uvicorn"
cd backend && uv run uvicorn app.main:app --reload

# Frontend
pkill -f "vite"
cd frontend && pnpm dev
```

### Clear Python cache

```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

---

## Data export/import (via API)

Requires a valid auth token.

```bash
# Export all recipes as JSON
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/export/all?format=json > recipes.json

# Import recipes from JSON
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@recipes.json" \
  http://localhost:8000/api/v1/import/recipes/json
```

---

## Security scanning

```bash
# Backend
cd backend && uv run pip-audit

# Frontend
cd frontend && pnpm audit
```

Dependabot is configured to open PRs for vulnerable dependencies automatically (see `.github/dependabot.yml`).
