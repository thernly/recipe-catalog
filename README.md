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
