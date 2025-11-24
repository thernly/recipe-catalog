# Frontend Dockerfile (multi-stage) for Recipe Catalog
# Stage 1: Build SvelteKit app
FROM node:25-alpine AS build
WORKDIR /frontend

# Install pnpm
RUN npm install -g pnpm

# Copy manifests and install dependencies
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy source
COPY frontend/. ./

# Build (produces static site in build/)
RUN pnpm build

# Stage 2: Nginx to serve static files and proxy API
FROM nginx:mainline-alpine AS runtime
WORKDIR /usr/share/nginx/html

# Copy built static assets
COPY --from=build /frontend/build ./

# Copy custom nginx config
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# No CMD override needed (default nginx startup)
