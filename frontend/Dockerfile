# Frontend Dockerfile (multi-stage) for Recipe Catalog
# Stage 1: Build SvelteKit app
FROM node:25-alpine AS build
WORKDIR /frontend

# Install pnpm
RUN npm install -g pnpm@10.17.1

# Copy manifests and install dependencies
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

# Copy source
COPY frontend/ ./
COPY VERSION /VERSION

# Build (produces static site in build/). APP_VERSION comes from docker-compose.
ARG APP_VERSION
ENV APP_VERSION=${APP_VERSION}
RUN pnpm build

# Stage 2: Nginx to serve static files and proxy API
FROM nginxinc/nginx-unprivileged:stable-alpine AS runtime
WORKDIR /usr/share/nginx/html

# Copy built static assets
COPY --from=build /frontend/build ./

# Copy custom nginx config
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

# No CMD override needed (default nginx startup)
