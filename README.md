# Recipe Catalog App

A privacy-focused web application for organizing and managing your personal recipe collection.

## 🎯 Overview

Recipe Catalog allows you to:
- Import recipes from websites via browser extension
- Manually add family recipes and personal favorites
- Organize recipes into custom collections
- Search and filter your recipe library
- Export your data anytime
- Access your recipes from any device

**Privacy First**: No tracking, no analytics, no third-party data sharing. Your recipes are yours.

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

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)
- pnpm or npm (package manager)

### Frontend Setup

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend runs on `http://localhost:5173`

### Backend Setup

Run this to generate a secret key for your .env file:

```python
import secrets
print(secrets.token_urlsafe(32))
```

or

```powerhell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

```bash
cd backend
uv run venv .venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate
uv sync
uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Database Setup

```bash
cd database
sqlite3 recipes.db < schema.sql
sqlite3 recipes.db < seed.sql  # Optional: Load test data
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
PUBLIC_API_URL=http://localhost:8000
VITE_APP_NAME=Recipe Catalog
```

### Backend (.env)
```env
DATABASE_URL=sqlite:///./recipes.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
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
pytest
pytest --cov=app tests/
```

## 📦 Deployment

### Cloudflare (Recommended)

**Frontend (Pages)**
```bash
cd frontend
pnpm build
wrangler pages deploy build
```

**Backend (Workers)**
```bash
cd backend
wrangler deploy
```

**Database (D1)**
```bash
wrangler d1 create recipe-catalog-db
wrangler d1 execute recipe-catalog-db --file=../database/schema.sql
```

### Docker (Alternative)

```bash
docker-compose up -d
```

## 🔒 Security

- Passwords hashed with bcrypt
- JWT-based authentication
- HTTPS only in production
- CORS properly configured
- SQL injection prevention via ORM
- XSS protection enabled
- Rate limiting on API endpoints

## 📖 Documentation

- [Product Requirements](docs/requirements/Recipe_Catalog_App_PRD_v1.1.md)
- [Wireframes](docs/requirements/Recipe_App_Wireframes.md)
- [User Flows](docs/requirements/Recipe_App_IA_and_User_Flows.md)
- [Design System](docs/requirements/Recipe_App_Themeable_Design_System.md)

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

**Version**: 1.0.0-alpha
**Status**: In Development
**Last Updated**: November 2025
