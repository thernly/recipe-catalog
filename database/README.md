# Database Setup

This directory contains database schema, migrations, and seed data for the Recipe Catalog application.

## Files

- **schema.sql** - Complete SQLite database schema (for reference)
- **seed.sql** - Sample data for development/testing
- **migrations/** - Alembic migration scripts

## Quick Start

The application uses SQLAlchemy with async SQLite (aiosqlite). The database is automatically created when you run the backend.

### Option 1: Automatic Setup (Recommended for Development)

The database tables are automatically created when you start the backend:

```bash
cd backend
uvicorn app.main:app --reload
```

This will create `recipes.db` in the backend directory with all required tables.

### Option 2: Using Alembic Migrations (Production)

For production or when you need version control of schema changes:

```bash
cd backend

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### Load Seed Data (Optional)

To load test data for development:

```bash
# Navigate to backend directory
cd backend

# Load seed data using Python
python -c "
import sqlite3
conn = sqlite3.connect('recipes.db')
with open('../database/seed.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()
print('Seed data loaded successfully!')
"
```

## Database Schema

### Users Table
Stores user account information.

### User Preferences Table
Stores user preferences (theme, default view, etc.).

### Recipes Table
Stores recipe data with full JSON content and metadata for search/filtering.

### Collections Table
User-created recipe collections.

### Recipe Collections Table
Junction table for many-to-many recipe-collection relationships.

## Migrations

### Creating a New Migration

After modifying SQLAlchemy models:

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Rolling Back

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

### Viewing Migration History

```bash
alembic history
alembic current
```

## Important Notes

- The application uses **aiosqlite** for async database operations
- Database file location: `backend/recipes.db` (by default)
- Change database location via `DATABASE_URL` environment variable
- For production, consider using PostgreSQL (architecture is PostgreSQL-ready)
- SQLite limitations:
  - `JSON` type is stored as TEXT with JSON validation
  - Some advanced PostgreSQL features not available
  - Good for MVP and small-to-medium deployments

## Migration to PostgreSQL

To migrate to PostgreSQL in the future:

1. Update `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/recipe_catalog
   ```

2. Install PostgreSQL driver:
   ```bash
   pip install asyncpg
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

The code is designed to work with both SQLite and PostgreSQL without changes!
