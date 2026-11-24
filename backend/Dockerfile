# Pin the dependency installer and keep build tools outside the runtime image.
FROM python:3.14-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.14-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DATABASE_URL=sqlite+aiosqlite:///./data/recipes.db \
    ENVIRONMENT=production
WORKDIR /app
RUN useradd --uid 10001 --create-home recipe && mkdir -p /app/data /app/logs && chown -R recipe:recipe /app
COPY --from=build /app/.venv /app/.venv
COPY --chown=recipe:recipe . /app
USER recipe
EXPOSE 8000
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=172.30.0.3"]
