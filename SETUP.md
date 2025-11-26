# Recipe Catalog Setup Guide

## Backend Setup

### Environment Configuration

The backend requires a `.env` file to run. Follow these steps:

1. Copy the example environment file:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Generate a secure SECRET_KEY:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. Edit `backend/.env` and update the following required fields:
   - `SECRET_KEY`: Use the generated key from step 2
   - `DATABASE_URL`: For local development, use `sqlite+aiosqlite:///./recipes.db`
   - `FRONTEND_URL`: Set to `http://localhost:5173` for local development
   - `OAUTH_REDIRECT_URI`: Set to `http://localhost:8000/api/v1/auth/callback`

4. Start the backend server:
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Common Issues

#### 404 Errors on Login/Providers Endpoints

If you're getting 404 errors when trying to log in, the most likely cause is that the backend server is not running or the `.env` file is missing/misconfigured.

**Solution:**
1. Verify the backend server is running: `curl http://localhost:8000/health`
2. Check that `backend/.env` exists and has a valid `SECRET_KEY`
3. Ensure `DATABASE_URL` is set correctly for your environment

## Frontend Setup

The frontend requires minimal configuration for local development:

1. The Vite dev server runs on port 5173 by default
2. No `.env` file is required for local development (defaults to `http://localhost:8000`)
3. Start the frontend:
   ```bash
   cd frontend
   npm install  # or pnpm install
   npm run dev
   ```

## Testing the Setup

1. Backend health check:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"ok"}`

2. Providers endpoint:
   ```bash
   curl http://localhost:8000/api/v1/auth/providers
   ```
   Should return: `[]` (empty array if no OAuth providers configured)

3. Open your browser and navigate to `http://localhost:5173`
