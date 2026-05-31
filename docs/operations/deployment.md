# Deployment Guide

## Option 1: Cloudflare (Recommended)

### Prerequisites

- Cloudflare account with Pages and Workers enabled
- `wrangler` CLI installed (`pnpm install -g wrangler`)
- Domain with DNS pointing to Cloudflare

### Step 1: Database (D1)

```bash
wrangler d1 create recipe-catalog-db
wrangler d1 execute recipe-catalog-db --file=./database/schema.sql
wrangler d1 list  # note the database ID for wrangler.toml
```

### Step 2: Backend (Workers)

```bash
cd backend
wrangler secret put SECRET_KEY
wrangler secret put GOOGLE_CLIENT_ID
wrangler secret put GOOGLE_CLIENT_SECRET
wrangler secret put MICROSOFT_CLIENT_ID
wrangler secret put MICROSOFT_CLIENT_SECRET
wrangler secret put GITHUB_CLIENT_ID
wrangler secret put GITHUB_CLIENT_SECRET
wrangler secret put OPENROUTER_API_KEY
wrangler deploy
```

### Step 3: Frontend (Pages)

```bash
cd frontend
echo "VITE_API_URL=https://api.yourdomain.com" > .env.production
pnpm build
wrangler pages deploy build
```

Or connect the GitHub repo in the Cloudflare dashboard for automatic deployments on push.

### Step 4: DNS

- Point your domain to Cloudflare Pages
- Add a CNAME record for the API subdomain pointing to the Workers deployment

---

## Option 2: Self-Hosted (Docker)

### Prerequisites

- Server with Docker and Docker Compose installed
- Domain with DNS configured
- Ports 80/443 open

### Step 1: Environment

```bash
cd backend && cp .env.example .env  # edit with production values
cd frontend && echo "VITE_API_URL=https://api.yourdomain.com" > .env
```

### Step 2: Deploy

```bash
docker-compose up -d
docker-compose logs -f          # verify startup
docker-compose exec backend uv run alembic upgrade head
```

### Step 3: nginx reverse proxy

```nginx
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

### Step 4: SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Updating

```bash
git pull
docker-compose build
docker-compose up -d
docker-compose exec backend uv run alembic upgrade head
```
