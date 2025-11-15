# Recipe Catalog App

A privacy-focused web application for organizing and managing your personal recipe collection.

## 🎯 Overview

Recipe Catalog allows you to:
- **Import recipes** from JSON files (browser extension coming soon)
- **Manually add** family recipes and personal favorites
- **Organize** recipes into custom collections with icons
- **Search and filter** your recipe library with advanced filters
- **Export your data** in JSON, Markdown, or plain text formats
- **Access** your recipes from any device with responsive design
- **Customize** appearance with two beautiful themes

**Privacy First**: No tracking, no analytics, no third-party data sharing. Your recipes are yours.

**Status**: ✅ MVP Complete and production-ready!

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
- **User Authentication** - Register, login, email verification, password reset
- **Recipe Management** - Full CRUD operations with comprehensive forms
- **Collections** - Organize recipes into custom collections with emoji icons
- **Search & Filter** - Advanced search with multiple filter criteria
- **Import/Export** - JSON file import and export in multiple formats
- **Themes** - Two beautiful themes (Classic Minimal & Professional Warm)
- **Responsive Design** - Works on mobile, tablet, and desktop
- **Soft Delete** - 30-day recovery period for deleted recipes

See [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) for detailed feature list.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)
- pnpm or npm (package manager)
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

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with secret key
cat > .env << EOF
DATABASE_URL=sqlite+aiosqlite:///./recipes.db
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
ENVIRONMENT=development
EOF

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
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
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Recipe Catalog
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

**Version**: 1.0.0-beta
**Status**: MVP Complete - Production Ready
**Last Updated**: November 15, 2025

## 🚢 Deployment

See [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md#-next-steps-for-production-deployment) for detailed deployment instructions including:
- Cloudflare deployment (recommended)
- Self-hosted Docker deployment
- Traditional cloud platforms

## 🔮 Roadmap

See the [PRD](docs/requirements/Recipe_Catalog_App_PRD_v1.1.md) for planned Phase 2+ features:
- Browser extension for recipe import
- Meal planning calendar
- Shopping list generation
- Cooking mode (hands-free view)
- Recipe sharing and social features
