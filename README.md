# Recipe Catalog App

A privacy-focused web application for organizing and managing your personal recipe collection.

## 🎯 Overview

Recipe Catalog allows you to:
- **Import recipes** from JSON files or generate with AI
- **Manually add** family recipes and personal favorites
- **Organize** recipes into custom collections with icons
- **Search and filter** your recipe library with advanced filters
- **Export your data** in JSON, Markdown, PDF, or plain text formats
- **Plan meals** with weekly meal planning calendar
- **Generate shopping lists** from recipes or meal plans
- **AI-powered features** for recipe generation and menu suggestions
- **Multi-user households** with invitation system
- **OAuth sign-in** with Google, Microsoft, or GitHub
- **Access** your recipes from any device with responsive design
- **Customize** appearance with two beautiful themes

**Privacy First**: No tracking, no analytics, no third-party data sharing. Your recipes are yours.

**Status**: ✅ Production-ready with advanced features!

## 🏗️ Tech Stack

### Frontend
- **SvelteKit** - Fast, modern web framework
- **Tailwind CSS** - Utility-first styling
- **TypeScript** - Type-safe development

### Backend
- **FastAPI** - High-performance Python API
- **SQLite/D1** - Lightweight database (PostgreSQL-ready)
- **Pydantic** - Data validation

### Deployment
- **Cloudflare Pages** - Frontend hosting
- **Cloudflare Workers** - Serverless API
- **Cloudflare D1** - Managed SQLite database

Alternative: Self-hosted on Proxmox with Docker

## 📁 Project Structure

```
recipe-catalog/
├── frontend/           # SvelteKit application
│   ├── src/
│   │   ├── routes/    # Pages and API routes
│   │   ├── lib/       # Components and utilities
│   │   └── app.html   # HTML template
│   ├── static/        # Static assets
│   └── package.json
│
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── models/    # Database models
│   │   ├── schemas/   # Pydantic schemas
│   │   └── core/      # Core utilities
│   ├── tests/
│   └── requirements.txt
│
├── database/          # Database schema and migrations
│   ├── schema.sql     # SQLite schema
│   ├── migrations/    # Alembic migrations
│   └── seed.sql       # Test data
│
└── docs/              # Documentation
    └── requirements/  # Product requirements
```

## ✨ Features

### Core Features (Implemented ✅)
- **User Authentication** - Register, login, email verification, password reset, OAuth/OIDC
- **OAuth Sign-In** - Google, Microsoft, and GitHub authentication
- **Recipe Management** - Full CRUD operations with comprehensive forms
- **Collections** - Organize recipes into custom collections with emoji icons
- **Search & Filter** - Advanced search with multiple filter criteria
- **Import/Export** - JSON import and export in JSON, Markdown, PDF, and plain text
- **Themes** - Two beautiful themes (Classic Minimal & Professional Warm)
- **Responsive Design** - Works on mobile, tablet, and desktop
- **Soft Delete** - 30-day recovery period for deleted recipes

### Advanced Features (Implemented ✅)
- **Multi-User Households** - Share recipes with family members via email invitations
- **Meal Planning** - Weekly meal planning calendar with drag-and-drop
- **Shopping Lists** - Generate shopping lists from recipes or meal plans
- **AI Recipe Generation** - Create recipes from ingredients using AI (OpenRouter)
- **AI Menu Suggestions** - Get personalized menu plans for multiple days
- **Custom Categories** - User-defined cuisines and recipe categories
- **Dietary Preferences** - Track and filter by dietary restrictions
- **PDF Export** - Professional PDF export for recipes and shopping lists
- **Rate Limiting** - API rate limiting for security and fair usage

See [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) for detailed feature list.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.13+ (for backend)
- pnpm or npm (package manager)
- uv (Python package manager) - Install from [astral.sh/uv](https://astral.sh/uv)
- SQLite (included with Python)

### Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install
# or: npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Start the development server
pnpm dev
# or: npm run dev
```

Frontend runs on `http://localhost:5173`

### First Steps

1. Open http://localhost:5173 in your browser
2. Click "Register" to create an account
3. Log in with your credentials
4. Start adding recipes!

### Backend Setup

```bash
cd backend

# Install dependencies with uv
uv sync

# Create .env file with secret key
cat > .env << EOF
DATABASE_URL=sqlite+aiosqlite:///./recipes.db
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
ENVIRONMENT=development

# Optional: OAuth providers (get credentials from provider dashboards)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/callback

# Optional: AI features (get API key from openrouter.ai)
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
EOF

# Run database migrations
uv run alembic upgrade head

# Start the server
uv run uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Database

The database is automatically created when you run the backend server. Migrations are handled by Alembic.

To load sample data (optional):
```bash
cd database
sqlite3 ../backend/recipes.db < seed.sql
```

## 🎨 Design System

The app features two beautiful themes:

**Classic Minimal** (Default)
- Primary: Charcoal (#3D4451)
- Accent: Saffron (#F59E0B)

**Professional Warm**
- Primary: Navy (#1E3A5F)
- Accent: Apricot (#F97316)

See `docs/requirements/Recipe_App_Themeable_Design_System.md` for complete design specifications.

## 📝 Environment Variables

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

### Backend (.env)
```env
DATABASE_URL=sqlite+aiosqlite:///./recipes.db
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
ENVIRONMENT=development

# Optional: Email configuration (for verification/password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Recipe Catalog
FRONTEND_URL=http://localhost:5173

# Optional: OAuth/OIDC providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/callback

# Optional: AI features via OpenRouter
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
AI_RATE_LIMIT_PER_HOUR=50

# Optional: Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

## 🧪 Testing

### Frontend Tests
```bash
cd frontend
pnpm test
pnpm test:unit
pnpm test:e2e
```

### Backend Tests
```bash
cd backend
uv run pytest
uv run pytest --cov=app tests/

# Run specific test file
uv run pytest tests/test_auth.py

# Run with verbose output
uv run pytest -v
```

## 🔧 Common Operations

### Database Migrations

**Create a new migration:**
```bash
cd backend
uv run alembic revision -m "description of changes"
# Edit the generated migration file in alembic/versions/
uv run alembic upgrade head
```

**Apply migrations:**
```bash
cd backend
# Apply all pending migrations
uv run alembic upgrade head

# Apply specific migration
uv run alembic upgrade <revision>

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
uv run alembic current
```

### Database Backup & Restore

**SQLite (Development):**
```bash
cd backend

# Create backup
cp recipes.db recipes.db.backup-$(date +%Y%m%d)

# Or use SQLite backup command
sqlite3 recipes.db ".backup recipes.db.backup"

# Restore from backup
cp recipes.db.backup recipes.db

# Export to SQL
sqlite3 recipes.db .dump > backup.sql

# Restore from SQL
sqlite3 recipes.db < backup.sql
```

**PostgreSQL (Production):**
```bash
# Create backup
pg_dump -U username -d recipe_catalog > backup.sql

# Create compressed backup
pg_dump -U username -d recipe_catalog | gzip > backup-$(date +%Y%m%d).sql.gz

# Restore from backup
psql -U username -d recipe_catalog < backup.sql

# Restore from compressed backup
gunzip -c backup.sql.gz | psql -U username -d recipe_catalog

# Automated daily backups (add to crontab)
0 2 * * * pg_dump -U username recipe_catalog | gzip > /backups/recipe-catalog-$(date +\%Y\%m\%d).sql.gz
```

### Database Maintenance

**Clean up soft-deleted records:**
```bash
cd backend
# Records marked as deleted are kept for 30 days
# Permanently delete records older than 30 days

sqlite3 recipes.db "DELETE FROM recipes WHERE deleted_at < datetime('now', '-30 days');"

# Or use Python script
uv run python -c "
from app.core.database import async_session_maker
from app.models.recipe import Recipe
from datetime import datetime, timedelta
import asyncio

async def cleanup():
    async with async_session_maker() as session:
        cutoff = datetime.utcnow() - timedelta(days=30)
        result = await session.execute(
            Recipe.__table__.delete().where(Recipe.deleted_at < cutoff)
        )
        await session.commit()
        print(f'Deleted {result.rowcount} old recipes')

asyncio.run(cleanup())
"
```

**Optimize database:**
```bash
# SQLite
sqlite3 recipes.db "VACUUM;"

# PostgreSQL
psql -U username -d recipe_catalog -c "VACUUM ANALYZE;"
```

### Monitoring & Logs

**View application logs:**
```bash
cd backend

# View live logs
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# View last 100 lines
tail -n 100 logs/app.log
```

**Monitor server health:**
```bash
# Check API health
curl http://localhost:8000/health

# Check with detailed info
curl http://localhost:8000/

# Monitor database size
ls -lh backend/recipes.db
```

### Data Export & Import

**Export all recipes:**
```bash
# Via API (requires authentication)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/export/all?format=json > recipes.json

# Direct database export
sqlite3 recipes.db "SELECT * FROM recipes WHERE deleted_at IS NULL;" \
  -header -csv > recipes.csv
```

**Import recipes:**
```bash
# Via API
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@recipes.json" \
  http://localhost:8000/api/import/json
```

### Troubleshooting

**Reset database (DESTRUCTIVE):**
```bash
cd backend

# Backup first!
cp recipes.db recipes.db.backup

# Drop all tables and recreate
rm recipes.db
uv run alembic upgrade head

# Or reset migrations
rm alembic/versions/*.py
uv run alembic revision --autogenerate -m "initial"
uv run alembic upgrade head
```

**Clear cache and restart:**
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Restart backend
pkill -f "uvicorn"
cd backend && uv run uvicorn app.main:app --reload

# Restart frontend
pkill -f "vite"
cd frontend && pnpm dev
```

**Check dependencies:**
```bash
# Backend
cd backend
uv pip list

# Frontend
cd frontend
pnpm list
```

## 📦 Deployment

### Production Deployment Guide

#### Prerequisites
- Domain name with DNS configured
- SSL certificate (automatically handled by Cloudflare or Let's Encrypt)
- Production database (PostgreSQL recommended for high-traffic deployments)
- Email service credentials (for password reset and verification)
- OAuth provider credentials (optional)

#### Option 1: Cloudflare (Recommended)

**Step 1: Database Setup (D1)**
```bash
# Create D1 database
wrangler d1 create recipe-catalog-db

# Run migrations
wrangler d1 execute recipe-catalog-db --file=./database/schema.sql

# Get database ID and update wrangler.toml
wrangler d1 list
```

**Step 2: Backend Deployment (Workers)**
```bash
cd backend

# Set production environment variables
wrangler secret put SECRET_KEY
wrangler secret put GOOGLE_CLIENT_ID
wrangler secret put GOOGLE_CLIENT_SECRET
# ... add other secrets

# Deploy to Cloudflare Workers
wrangler deploy
```

**Step 3: Frontend Deployment (Pages)**
```bash
cd frontend

# Update API URL for production
echo "VITE_API_URL=https://api.yourdomain.com" > .env.production

# Build and deploy
pnpm build
wrangler pages deploy build

# Or use GitHub integration (recommended)
# Push to GitHub and connect repo in Cloudflare dashboard
```

**Step 4: Configure DNS**
- Point your domain to Cloudflare Pages
- Add CNAME record for API subdomain

#### Option 2: Self-Hosted (Docker)

**Step 1: Prepare Server**
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose
```

**Step 2: Configure Environment**
```bash
# Create production .env files
cd backend
cp .env.example .env
# Edit .env with production values

cd ../frontend
echo "VITE_API_URL=https://api.yourdomain.com" > .env
```

**Step 3: Deploy with Docker**
```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Run migrations
docker-compose exec backend alembic upgrade head
```

**Step 4: Set Up Reverse Proxy (nginx)**
```nginx
# /etc/nginx/sites-available/recipe-catalog
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Step 5: SSL Setup (Let's Encrypt)**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

#### Option 3: Traditional Cloud Platforms

**AWS, Google Cloud, Azure, DigitalOcean, etc.**

1. **Backend**: Deploy as containerized application or serverless function
2. **Frontend**: Deploy to static hosting (S3, Cloud Storage, etc.)
3. **Database**: Use managed PostgreSQL service (RDS, Cloud SQL, etc.)
4. **CDN**: CloudFront, Cloud CDN, or Azure CDN

Refer to your platform's documentation for specific deployment steps.

## 🔒 Security

- Passwords hashed with bcrypt
- JWT-based authentication with CSRF protection
- HTTPS only in production
- CORS properly configured
- SQL injection prevention via ORM
- XSS protection with input sanitization
- Rate limiting on API endpoints
- Security headers (X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, CSP)
- Automated dependency scanning with Dependabot

### Dependency Security Scanning

We use automated tools to keep dependencies secure and up-to-date:

**Automated Scanning (GitHub Dependabot)**
- Dependabot is configured to check for vulnerabilities weekly
- Automatically creates pull requests for security updates
- See `.github/dependabot.yml` for configuration

**Manual Scanning (Monthly)**
1. Install pip-audit for backend scanning:
   ```bash
   cd backend
   uv pip install pip-audit
   ```

2. Run security audit:
   ```bash
   uv run pip-audit
   ```

3. Review and address any vulnerabilities found

4. Update frontend dependencies:
   ```bash
   cd frontend
   pnpm audit
   pnpm update
   ```

**Monthly Maintenance Tasks**
- Review and merge Dependabot PRs
- Run manual security scans with pip-audit and pnpm audit
- Test application after updates
- Update dependency versions in lockfiles

**Known Issues**
- `ecdsa` (dependency of `python-jose`): Security advisory GHSA-wj6h-64fc-37mp
  - Future consideration: Replace `python-jose` with `PyJWT` for better security
  - Tracked in tasks backlog

## 📖 Documentation

- **[Implementation Status](IMPLEMENTATION_STATUS.md)** - Complete feature list and progress
- [Product Requirements](docs/requirements/Recipe_Catalog_App_PRD_v1.1.md) - Full PRD
- [Wireframes](docs/requirements/Recipe_App_Wireframes.md) - UI wireframes
- [User Flows](docs/requirements/Recipe_App_IA_and_User_Flows.md) - User flows and IA
- [Design System](docs/requirements/Recipe_App_Themeable_Design_System.md) - Design tokens and themes

## 🤝 Contributing

This is a personal project, but suggestions and bug reports are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - Feel free to use this for your own recipe organization needs!

## 🙏 Acknowledgments

Built with ❤️ for home cooks who value privacy and organization.

---

**Version**: 1.0.0
**Status**: Production Ready - Advanced Features Included
**Last Updated**: November 18, 2025

## 🚢 Deployment

See [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md#-next-steps-for-production-deployment) for detailed deployment instructions including:
- Cloudflare deployment (recommended)
- Self-hosted Docker deployment
- Traditional cloud platforms

## 🔮 Roadmap

See the [PRD](docs/requirements/Recipe_Catalog_App_PRD_v1.1.md) for planned future features:
- Browser extension for recipe import
- Cooking mode (hands-free view)
- Recipe scaling and unit conversion
- Nutritional information tracking
- Recipe sharing and social features
- Voice control for hands-free cooking
