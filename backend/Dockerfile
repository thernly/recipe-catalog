# Backend Dockerfile for Recipe Catalog
# Production-oriented image

FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System dependencies (build-essential only if native extensions appear later)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies (fallback if lock file absent)
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Copy application code
COPY . /app

# Create data directory for SQLite persistence mounted as volume
RUN mkdir -p /app/data

# Environment defaults (override via compose env_file)
ENV PORT=8000 \
    DATABASE_URL=sqlite+aiosqlite:///./data/recipes.db

EXPOSE 8000

# Run with uv to ensure virtual env isolation
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
