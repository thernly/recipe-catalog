# Recipe Catalog - AI Agent Guidelines

## Project Overview

Recipe Catalog is a privacy-focused web application for organizing and managing personal recipe collections. The application uses a modern full-stack architecture with a SvelteKit frontend and FastAPI backend.

**Current Status**: ✅ MVP Complete and production-ready

**Core Philosophy**: Privacy First - No tracking, no analytics, no third-party data sharing.

---

## Technology Stack

### Frontend
- **Framework**: SvelteKit (TypeScript)
- **Styling**: Tailwind CSS with custom CSS variables for theming
- **State Management**: Svelte stores (`auth.ts`, `collections.ts`)
- **Build Tool**: Vite
- **Package Manager**: pnpm (preferred) or npm

### Backend
- **Framework**: FastAPI (Python 3.13+)
- **Database**: SQLite with SQLAlchemy async ORM (PostgreSQL-ready)
- **Async Support**: aiosmtplib, aiosqlite
- **Authentication**: JWT with argon2 password hashing
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **Rate Limiting**: SlowAPI

### Development Tools
- **Backend Linting**: Ruff
- **Backend Type Checking**: mypy
- **Frontend Linting**: ESLint
- **Frontend Formatting**: Prettier

---

## Project Structure

```
recipe-catalog/
├── frontend/                    # SvelteKit application
│   ├── src/
│   │   ├── routes/             # File-based routing
│   │   │   ├── auth/           # Authentication pages
│   │   │   ├── dashboard/      # Dashboard view
│   │   │   ├── recipes/        # Recipe CRUD pages
│   │   │   ├── collections/    # Collection pages
│   │   │   ├── settings/       # User settings
│   │   │   ├── import/         # Recipe import
│   │   │   └── export/         # Recipe export
│   │   ├── lib/
│   │   │   ├── api/            # API client modules
│   │   │   ├── components/     # Svelte components
│   │   │   ├── stores/         # State management
│   │   │   └── config.ts       # Configuration
│   │   ├── app.css             # Global styles & themes
│   │   └── app.html            # HTML template
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── api/                # API route handlers
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── recipes.py      # Recipe CRUD
│   │   │   ├── collections.py  # Collection management
│   │   │   ├── users.py        # User profile/preferences
│   │   │   ├── import_recipes.py # Recipe import
│   │   │   └── export.py       # Recipe export
│   │   ├── core/               # Core utilities
│   │   │   ├── config.py       # Settings management
│   │   │   ├── database.py     # Database setup
│   │   │   ├── security.py     # Auth utilities
│   │   │   ├── deps.py         # FastAPI dependencies
│   │   │   └── email.py        # Email sending
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── recipe.py
│   │   │   ├── collection.py
│   │   │   └── token.py
│   │   ├── schemas/            # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── recipe.py
│   │   │   └── collection.py
│   │   ├── services/           # Business logic
│   │   └── utils/              # Utility functions
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Test suite
│   ├── pyproject.toml          # Python dependencies
│   └── main.py                 # Application entry point
│
├── database/                    # Database schema
│   ├── schema.sql              # SQLite schema definition
│   └── seed.sql                # Test data
│
└── docs/                        # Documentation
    ├── requirements/           # Product requirements
    ├── assessments/            # Code assessments
    └── issues/                 # Known issues
```

---

## Key Architectural Patterns

### Frontend Patterns

1. **File-Based Routing**: SvelteKit uses the filesystem for routing
   - `+page.svelte` = page component
   - `+layout.svelte` = layout wrapper
   - `[id]/` = dynamic route segments

2. **Store-Based State**: Authentication and collections use Svelte stores
   - `auth.ts`: User session, login/logout, token management
   - `collections.ts`: Collection list and CRUD operations

3. **API Client Pattern**: Centralized API calls through `lib/api/` modules
   - `client.ts`: Base fetch wrapper with auth headers
   - Individual modules for different resources (recipes, users, collections)

4. **Theme System**: CSS custom properties with `data-theme` attribute
   - Two themes: "classic" (Charcoal + Saffron) and "professional" (Navy + Apricot)
   - Theme switcher component persists preference to localStorage

5. **Component Organization**:
   - Reusable UI components in `lib/components/`
   - Feature-specific components in subdirectories (recipe/, settings/, export/)

### Backend Patterns

1. **Async Everything**: All database operations use async/await
   - AsyncSession for database
   - Async route handlers
   - Async email sending

2. **Dependency Injection**: FastAPI's dependency system
   - `get_db()`: Database session dependency
   - `get_current_user()`: Authentication dependency
   - `get_current_active_user()`: Active user check

3. **Schema Validation**: Pydantic schemas separate from SQLAlchemy models
   - Models: Database representation (`app/models/`)
   - Schemas: API request/response validation (`app/schemas/`)

4. **Soft Delete Pattern**: Recipes and collections have `deleted_at` field
   - 30-day recovery period before permanent deletion
   - Trash functionality for users to restore items

5. **Rate Limiting**: SlowAPI for endpoint protection
   - Configured per-endpoint
   - Uses client IP for tracking

---

## Authentication & Security

### Authentication Flow
1. User registers with email/password
2. Email verification token sent
3. User verifies email via token link
4. Login generates JWT access token
5. Token stored in localStorage (frontend) and passed as Bearer token

### Password Security
- **Hashing**: Argon2 (industry standard)
- **Reset Flow**: Time-limited reset tokens via email
- **Validation**: Minimum length requirements

### Authorization
- **JWT Tokens**: Short-lived access tokens
- **User Scopes**: Currently single-user accounts (multi-user planned)
- **Protected Routes**: Require `get_current_active_user` dependency

---

## Database Schema

### Core Models
1. **User**: User accounts and authentication
2. **UserPreferences**: Theme, default view, cuisines, categories
3. **Recipe**: Recipe data with ingredients, instructions, metadata
4. **Collection**: User-created recipe collections
5. **RecipeCollection**: Many-to-many relationship
6. **VerificationToken**: Email verification
7. **PasswordResetToken**: Password reset flow

### Key Relationships
- User ← (1:many) → Recipe
- User ← (1:many) → Collection
- Recipe ← (many:many) → Collection
- User ← (1:1) → UserPreferences

---

## Known Issues & Technical Debt

### Current Issues (from CODEBASE_ANALYSIS.md)

1. **Navigation Inconsistency**
   - Navbar missing from recipe detail pages (`/recipes/[id]`)
   - Navbar missing from settings page
   - Navbar missing from collection detail pages
   - Theme toggle only available on landing page (disappears after login)

2. **Unused Components**
   - `CollectionsSidebar.svelte` exists but is not used in any page layout
   - Component has full functionality but no integration points

3. **Layout Structure**
   - Root layout (`+layout.svelte`) is empty (only `<slot />`)
   - Each page imports Navbar individually (inconsistent)
   - Should consider unified layout approach

### Planned Enhancements (from PRD v2.1)

**Next Feature Wave**:
1. Identity Provider Authentication (Google, Microsoft SSO)
2. Household/Group Multi-User Tenancy (max 10 members)
3. Weekly Meal Planning (calendar-style)
4. Shopping Lists (from recipes and meal plans)
5. AI-Generated Recipes (from available ingredients)
6. AI-Generated Menu Suggestions (dietary preferences)
7. Additional UI Themes (Dark Mode, High Contrast)
8. PDF Export for Recipes & Collections

**Explicitly Out of Scope**:
- Social media features
- Public recipe sharing
- Community/social graph features
- Browser extension (separate project)

---

## Development Workflow

### Running Locally

**Backend**:
```powershell
cd backend
# Install dependencies with uv (recommended)
uv sync

# Run development server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run type checker
uv run mypy app/
```

**Frontend**:
```powershell
cd frontend
# Install dependencies
pnpm install

# Run development server
pnpm dev

# Build for production
pnpm build

# Run linter
pnpm lint

# Format code
pnpm format
```

### Environment Variables

**Backend** (`.env` in `backend/`):
```
DATABASE_URL=sqlite+aiosqlite:///./recipes.db
SECRET_KEY=<your-secret-key>
ALLOWED_ORIGINS=["http://localhost:5173"]
SMTP_HOST=<smtp-server>
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<password>
```

**Frontend** (`.env` in `frontend/`):
```
PUBLIC_API_URL=http://localhost:8000
```

### Database Migrations

Using Alembic:
```powershell
cd backend
# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

---

## API Endpoints Reference

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `POST /api/auth/verify-email/{token}` - Verify email
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password/{token}` - Reset password

### Users
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update profile
- `GET /api/users/me/preferences` - Get preferences
- `PUT /api/users/me/preferences` - Update preferences
- `GET /api/users/me/stats` - Get user statistics
- `DELETE /api/users/me` - Delete account

### Recipes
- `GET /api/recipes` - List recipes (with filters, search, pagination)
- `POST /api/recipes` - Create recipe
- `GET /api/recipes/{id}` - Get recipe details
- `PUT /api/recipes/{id}` - Update recipe
- `DELETE /api/recipes/{id}` - Soft delete recipe
- `GET /api/recipes/trash` - List deleted recipes
- `POST /api/recipes/{id}/restore` - Restore deleted recipe
- `DELETE /api/recipes/{id}/permanent` - Permanently delete

### Collections
- `GET /api/collections` - List collections
- `POST /api/collections` - Create collection
- `GET /api/collections/{id}` - Get collection with recipes
- `PUT /api/collections/{id}` - Update collection
- `DELETE /api/collections/{id}` - Soft delete collection
- `POST /api/collections/{id}/recipes/{recipe_id}` - Add recipe
- `DELETE /api/collections/{id}/recipes/{recipe_id}` - Remove recipe

### Import/Export
- `POST /api/import/json` - Import recipes from JSON
- `GET /api/export/json` - Export all recipes as JSON
- `GET /api/export/markdown` - Export as Markdown
- `GET /api/export/text` - Export as plain text

---

## Coding Guidelines

### General Principles
1. **Privacy First**: No tracking, no analytics, minimal data collection
2. **Type Safety**: Use TypeScript (frontend) and type hints (backend)
3. **Async by Default**: All I/O operations should be async
4. **Error Handling**: Proper exception handling and user-friendly errors
5. **Testing**: Write tests for critical business logic

### Frontend Guidelines
- Use TypeScript for all new code
- Follow Svelte component conventions
- Use Tailwind utility classes (avoid custom CSS when possible)
- Maintain theme compatibility (use CSS variables)
- Keep components small and focused
- Use stores for shared state, props for component communication

### Backend Guidelines
- Use async/await for all database operations
- Validate input with Pydantic schemas
- Use dependency injection for database sessions and auth
- Follow RESTful API conventions
- Return appropriate HTTP status codes
- Log errors but don't expose internals to users

### Python Style
- Follow PEP 8 (enforced by Ruff)
- Use type hints for function signatures
- Docstrings for public APIs
- Keep functions focused and testable
- Use f-strings for string formatting

### TypeScript/JavaScript Style
- Use `const` by default, `let` when needed, avoid `var`
- Prefer async/await over promises/callbacks
- Use optional chaining (`?.`) and nullish coalescing (`??`)
- Interface for object shapes
- Avoid `any` type

---

## Testing Strategy

### Backend Testing
- **Framework**: pytest with pytest-asyncio
- **Coverage**: pytest-cov
- **Test Database**: Separate test database (in-memory SQLite)
- **Fixtures**: Defined in `conftest.py`

**Current Tests**:
- Authentication flows (register, login, verify)
- User CRUD operations
- Recipe CRUD operations
- Collection management

**To Add**:
- Import/export functionality
- Email sending (mocked)
- Rate limiting
- Soft delete and restore

### Frontend Testing
- **Framework**: Not yet configured (TODO)
- **Recommended**: Vitest + Testing Library

---

## Deployment Targets

### Primary: Cloudflare
- **Frontend**: Cloudflare Pages
- **Backend**: Cloudflare Workers (with Hono adapter)
- **Database**: Cloudflare D1 (managed SQLite)

### Alternative: Self-Hosted
- **Platform**: Proxmox/Docker
- **Frontend**: Static files via Nginx
- **Backend**: Uvicorn behind Nginx reverse proxy
- **Database**: SQLite or PostgreSQL

---

## AI Agent Task Guidelines

When working on this codebase, AI agents should:

### 1. Understand Context First
- Read relevant files before making changes
- Check both frontend and backend when changes affect both
- Review existing patterns and follow them
- Consult CODEBASE_ANALYSIS.md for known issues

### 2. Make Consistent Changes
- Match existing code style and patterns
- Use the same libraries and tools already in place
- Maintain theme compatibility when touching UI
- Update both implementation and tests

### 3. Consider Privacy
- Never add analytics or tracking
- Minimize data collection
- Respect user data ownership
- Default to secure options

### 4. Handle Errors Gracefully
- Validate input thoroughly
- Return helpful error messages
- Log errors for debugging
- Don't expose internal details to users

### 5. Test Your Changes
- Run linters before committing
- Test both happy path and edge cases
- Verify database migrations work
- Check UI in both themes

### 6. Document Decisions
- Update relevant documentation
- Add comments for complex logic
- Update API documentation if endpoints change
- Note any breaking changes

### 7. Known Issue Areas to Watch
- Navigation consistency (navbar appearing on all pages)
- Theme switcher availability (should be in settings)
- CollectionsSidebar integration (currently unused)
- Layout structure (consider unified approach)

---

## File Path Conventions

### Absolute Paths
When referencing files in this codebase, use absolute paths from workspace root:
- ✅ `c:\source\recipe-catalog\frontend\src\lib\components\Navbar.svelte`
- ✅ `c:\source\recipe-catalog\backend\app\main.py`

### Import Paths
**Frontend**: Use `$lib` alias for src/lib
```typescript
import { auth } from '$lib/stores/auth';
import Navbar from '$lib/components/Navbar.svelte';
```

**Backend**: Use absolute imports from app package
```python
from app.core.database import get_db
from app.models.user import User
from app.schemas.recipe import RecipeCreate
```

---

## Common Tasks

### Adding a New API Endpoint
1. Define Pydantic schema in `app/schemas/`
2. Create/update model in `app/models/` if needed
3. Add route handler in appropriate `app/api/` file
4. Add to router with proper dependencies
5. Update frontend API client in `lib/api/`
6. Add tests in `tests/`

### Adding a New Page
1. Create `+page.svelte` in `routes/` directory
2. Import and use Navbar component (if authenticated page)
3. Add to navigation if needed
4. Implement API calls using `lib/api/` clients
5. Use theme CSS variables for styling
6. Add auth guard if private page

### Adding a New Component
1. Create `.svelte` file in `lib/components/`
2. Use TypeScript for props typing
3. Use Tailwind classes with theme CSS variables
4. Export reusable components
5. Document props with JSDoc comments

### Modifying Database Schema
1. Update SQLAlchemy model in `app/models/`
2. Update Pydantic schemas in `app/schemas/`
3. Generate Alembic migration
4. Test migration up and down
5. Update seed data if needed

---

## Resources & References

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SvelteKit Documentation**: https://kit.svelte.dev/
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Pydantic V2**: https://docs.pydantic.dev/latest/
- **Tailwind CSS**: https://tailwindcss.com/docs

---

## Contact & Support

This is a privacy-focused personal project. For questions or contributions:
- Check existing documentation in `docs/`
- Review known issues in `docs/issues/`
- Consult product requirements in `docs/requirements/`

---

**Last Updated**: November 16, 2025  
**Document Version**: 1.0
