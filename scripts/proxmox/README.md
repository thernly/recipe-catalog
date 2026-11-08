# Recipe Catalog - Proxmox LXC Deployment

This directory contains the scripts for deploying Recipe Catalog to a Proxmox LXC container running Debian 12, and for updating it afterwards.

## Available Scripts

### `deploy-lxc.sh` - Automated LXC Deployment

Installs Recipe Catalog on a fresh Debian 12 container:

- System package updates and dependencies (git, nginx, certbot, sqlite3)
- Node.js 24.x and pnpm
- UV package manager and Python 3.13 via UV (pre-built binaries)
- Application code (Git clone, or files already in `/opt/recipe-catalog`)
- Backend and frontend configuration, database migrations
- Nginx reverse proxy and a systemd service for the backend
- Optional SSL/TLS with Let's Encrypt
- Optional UFW firewall (interactive mode only)

It runs interactively (prompts, recommended for first-time setup) or non-interactively (for automation), logs to `/var/log/recipe-catalog-deployment.log`, and checks backend health at the end.

### `update-app.sh` - Automated Application Updates

Updates an existing install to the latest code, with a database backup first. See [Updating the Application](#updating-the-application).

## Creating the Container

In the Proxmox web UI, click **Create CT**: Debian 12 template, 2+ cores, 2048MB+ memory (4096MB recommended), 8GB+ disk (16GB recommended), bridged network (static IP or DHCP), **Start at boot** enabled. Then `pct enter <container-id>` (or SSH in) and run the deploy script.

## Prerequisites

1. **LXC container** as described above.
2. **Access**: root access to the container and an internet connection.
3. **DNS (for HTTPS)**: a domain name pointed at the server. Production mode (the default) requires it; see below.

## Quick Start

### Interactive Deployment (Recommended)

The script lives in the repository, so get the code onto the container first (clone it, or copy it to `/opt/recipe-catalog`), then:

```bash
# As root on your LXC container
cd /opt/recipe-catalog/scripts/proxmox
bash deploy-lxc.sh
```

The script will prompt you for:

- Server IP address or domain name
- Git repository URL (or `local` to use existing files)
- SSL/TLS configuration (domain name)
- SMTP email settings
- Firewall setup (optional)

### Non-Interactive Deployment

```bash
bash deploy-lxc.sh \
    --non-interactive \
    --repo-url https://github.com/yourusername/recipe-catalog.git \
    --server-ip 192.168.1.100 \
    --domain recipes.example.com
```

In non-interactive mode the SMTP password is left empty and the firewall step is skipped; set them afterwards.

### Production vs. Development Mode

The script writes `ENVIRONMENT=production` to the backend `.env` by default (override with `--development` or `DEPLOY_ENVIRONMENT=development`). Production mode marks auth cookies `Secure`, which browsers only send over HTTPS, so the script refuses to run in production without `--domain`.

For a plain-HTTP install on a trusted local network, pass `--development` instead of `--domain`. That writes `ENVIRONMENT=development`: cookies are not marked `Secure` and the backend uses a relaxed CSP. In interactive mode, declining SSL offers development mode. Once you add HTTPS, change the line to `ENVIRONMENT=production` and restart the backend (`update-app.sh` warns if SSL is configured but the `.env` still says `development`).

### Using Existing Files

If you've already copied the application files to `/opt/recipe-catalog`:

```bash
bash deploy-lxc.sh --repo-url local
```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--non-interactive` | Run without prompts (uses defaults) | `--non-interactive` |
| `--repo-url <url>` | Git repository URL or 'local' | `--repo-url https://github.com/user/repo.git` |
| `--server-ip <ip>` | Server IP address or domain | `--server-ip 192.168.1.100` |
| `--domain <hostname>` | Configure HTTPS for production (required unless `--development`) | `--domain recipes.example.com` |
| `--development` | Local plain-HTTP development mode | `--development` |
| `--skip-python` | Skip Python 3.13 installation | `--skip-python` |
| `--help` | Show help message | `--help` |

## What The Script Does

### 1. System Preparation

- Updates all system packages
- Installs git, nginx, certbot (with the nginx plugin), sqlite3, curl, wget, gnupg
- Installs Node.js 24.x (NodeSource) and pnpm 10.17.1, unless already present

### 2. Application Setup

- Creates the `recipe-app` system user
- Creates `/opt/recipe-catalog` (with `backend/data` and `backend/logs`)
- Clones the repository (or pulls if already cloned), or uses existing files
- Installs UV to `/home/recipe-app/.local/bin/uv` (checksum-verified release)
- Installs Python 3.13 with UV and pins the project to it

### 3. Backend Configuration

- Installs Python dependencies with `uv sync --frozen`
- Generates `backend/.env` (mode 600) with:
  - Random `SECRET_KEY`
  - SQLite database at `data/recipes.db`
  - `ALLOWED_ORIGINS` and `FRONTEND_URL` set to the public origin (`https://<domain>` or `http://<server-ip>`)
  - `OAUTH_REDIRECT_BASE_URL` set to `<public origin>/api/v1/auth`
  - SMTP settings
  - `ENVIRONMENT` (`production` or `development`, see above) and `DEBUG=False`
  - Rate limiting, upload limits, logging
- Runs `alembic upgrade head` to create the database

### 4. Frontend Configuration

- Installs dependencies with `pnpm install --frozen-lockfile`
- Generates `frontend/.env` with `VITE_API_URL`
- Builds the production bundle

### 5. Web Server Setup

- Configures Nginx to serve the frontend build and proxy `/api` to the backend on `127.0.0.1:8000`
- Adds security headers
- With `--domain`, obtains a Let's Encrypt certificate for the domain and `www.` subdomain via `certbot --nginx` (the SMTP user is used as the contact email)

### 6. Service Management

- Creates and enables the `recipe-catalog-backend` systemd service (uvicorn, 1 worker)
- Starts the backend and Nginx
- Polls `http://127.0.0.1:8000/health`

### 7. Firewall (Optional, interactive only)

- Installs UFW and opens ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

## Post-Deployment

1. **Access the application** at `https://<domain>` (or `http://<server-ip>` in development mode).

2. **Check service status**

   ```bash
   systemctl status recipe-catalog-backend
   systemctl status nginx
   curl http://127.0.0.1:8000/health
   ```

3. **View logs**

   ```bash
   # Deployment log
   cat /var/log/recipe-catalog-deployment.log

   # Backend application logs
   journalctl -u recipe-catalog-backend -f

   # Nginx logs
   tail -f /var/log/nginx/recipe-catalog-error.log
   ```

4. **Register the first user** in the browser. A verification email is sent if SMTP is configured.

The interactive API docs (`/docs`) are disabled because the generated `.env` sets `DEBUG=False`, and Nginx only proxies `/api` to the backend.

## Manual Configuration

### Backend Environment Variables

Edit `/opt/recipe-catalog/backend/.env`, then `systemctl restart recipe-catalog-backend`.

Important settings:

- `ENVIRONMENT`: `production` (Secure cookies, strict CSP; needs HTTPS) or `development` (plain HTTP on a trusted network). See [Production vs. Development Mode](#production-vs-development-mode).
- `ALLOWED_ORIGINS`, `FRONTEND_URL`: must match the URL users browse to.
- `OAUTH_REDIRECT_BASE_URL`: base for OAuth callbacks, normally `https://<domain>/api/v1/auth`. Register `<that>/google/callback` (likewise `/microsoft/callback`, `/github/callback`) with each provider you enable.
- `SECRET_KEY`: keep it secret and unique.

### Email Providers

Set these in `backend/.env`, then restart the backend:

```bash
# Gmail (needs 2FA and an App Password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com

# SendGrid: SMTP_HOST=smtp.sendgrid.net, SMTP_USER=apikey, SMTP_PASSWORD=<api key>
# Mailgun:  SMTP_HOST=smtp.mailgun.org,  SMTP_USER=postmaster@<domain>, SMTP_PASSWORD=<password>
```

### Frontend Environment Variables

Edit `/opt/recipe-catalog/frontend/.env`, then rebuild:

```bash
su - recipe-app
cd /opt/recipe-catalog/frontend
pnpm build
exit
systemctl reload nginx
```

### Nginx Configuration

Edit `/etc/nginx/sites-available/recipe-catalog`, then:

```bash
nginx -t
systemctl reload nginx
```

## Updating the Application

### Automated Update (Recommended)

```bash
# Standard update from git (branch main)
bash /opt/recipe-catalog/scripts/proxmox/update-app.sh

# Update from a specific branch
bash /opt/recipe-catalog/scripts/proxmox/update-app.sh --branch develop

# Update without pulling from git
bash /opt/recipe-catalog/scripts/proxmox/update-app.sh --skip-git

# Update without backup (not recommended)
bash /opt/recipe-catalog/scripts/proxmox/update-app.sh --skip-backup
```

Run as root. Options: `--skip-git`, `--skip-backup`, `--branch <name>` (default `main`), `--help`.

What it does:

1. Backs up the database to `/opt/recipe-catalog-backups/recipes-<timestamp>.db` (keeps the last 10) and copies both `.env` files there
2. Stops the backend service
3. Fixes repository ownership, moves the `.env` files aside, stashes local changes, checks out the branch and pulls, then restores the `.env` files
4. Verifies `backend/.env` exists, and warns if SSL is configured but `ENVIRONMENT` is still `development`
5. Runs `uv sync --frozen` and `alembic upgrade head`
6. Runs a SQLite integrity check; on failure, restores the backup and stops
7. Runs `pnpm install --frozen-lockfile` and `pnpm build`
8. Starts the backend, reloads Nginx, and checks `/health`

It logs to `/var/log/recipe-catalog-update.log` and prints rollback commands at the end.

### Manual Update

```bash
systemctl stop recipe-catalog-backend

cd /opt/recipe-catalog
sudo -u recipe-app git pull

cd backend
sudo -u recipe-app /home/recipe-app/.local/bin/uv sync --frozen
sudo -u recipe-app /home/recipe-app/.local/bin/uv run alembic upgrade head

cd ../frontend
sudo -u recipe-app pnpm install --frozen-lockfile
sudo -u recipe-app pnpm build

systemctl start recipe-catalog-backend
systemctl reload nginx
```

## Scheduled Backups

`update-app.sh` backs up the database before each update. For daily backups as well:

```bash
cat > /usr/local/bin/backup-recipe-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
mkdir -p "$BACKUP_DIR"
cp /opt/recipe-catalog/backend/data/recipes.db "$BACKUP_DIR/recipes-$(date +%Y%m%d-%H%M%S).db"
find "$BACKUP_DIR" -name "recipes-*.db" -mtime +30 -delete
EOF
chmod +x /usr/local/bin/backup-recipe-db.sh
echo "0 2 * * * /usr/local/bin/backup-recipe-db.sh" | crontab -
```

## Hardening

- Firewall: `apt install ufw`, allow 22/80/443 only, `ufw enable` (the deploy script offers this interactively).
- `apt install fail2ban` and enable it.
- In `/etc/ssh/sshd_config`: `PermitRootLogin no`, `PasswordAuthentication no` (use SSH keys).
- Keep the system updated with `apt update` and `apt upgrade`.

## Troubleshooting

### Git Permission Errors During Update

If you see `error: insufficient permission for adding an object to repository database .git/objects`:

```bash
chown -R recipe-app:recipe-app /opt/recipe-catalog
bash /opt/recipe-catalog/scripts/proxmox/update-app.sh
```

`update-app.sh` already fixes ownership before pulling; run the `chown` by hand if you hit this with manual git commands.

### Script Fails During Python Installation

```bash
su - recipe-app
~/.local/bin/uv --version
~/.local/bin/uv python install 3.13
~/.local/bin/uv python list
```

Then check `/var/log/recipe-catalog-deployment.log`.

### Backend Service Won't Start

```bash
journalctl -u recipe-catalog-backend -n 50

# Test manually
su - recipe-app
cd /opt/recipe-catalog/backend
~/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend refuses to start if the database is behind the latest migration; run `uv run alembic upgrade head` in `backend/` as `recipe-app`.

### Frontend Build Fails

```bash
su - recipe-app
cd /opt/recipe-catalog/frontend
pnpm install --frozen-lockfile
pnpm build
```

### Can't Access Application or Can't Stay Logged In

```bash
systemctl status recipe-catalog-backend
systemctl status nginx
ss -tulpn | grep -E ':(80|443|8000)'
nginx -t
ufw status
```

If the page loads but login doesn't stick over plain HTTP, `ENVIRONMENT` is probably `production` (Secure cookies); see [Production vs. Development Mode](#production-vs-development-mode).

## Uninstalling

```bash
systemctl stop recipe-catalog-backend
systemctl disable recipe-catalog-backend
rm /etc/systemd/system/recipe-catalog-backend.service
systemctl daemon-reload

rm /etc/nginx/sites-available/recipe-catalog
rm /etc/nginx/sites-enabled/recipe-catalog
systemctl reload nginx

rm -rf /opt/recipe-catalog /opt/recipe-catalog-backups
userdel -r recipe-app

rm /var/log/recipe-catalog-deployment.log /var/log/recipe-catalog-update.log
rm /var/log/nginx/recipe-catalog-*.log
```
