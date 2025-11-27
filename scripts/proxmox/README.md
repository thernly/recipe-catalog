# Recipe Catalog - Deployment Scripts

This directory contains automation scripts for deploying Recipe Catalog.

## Available Scripts

### `deploy-lxc.sh` - Automated LXC Deployment

Fully automated deployment script for installing Recipe Catalog on a Proxmox LXC container running Debian 12.

### `update-app.sh` - Automated Application Updates

Automated update script for safely updating Recipe Catalog to the latest version with automatic database backups.

#### Features

✅ **Automated Installation**

- System package updates and dependency installation
- Node.js 20.x and pnpm installation
- UV package manager setup
- Python 3.13 installation via UV (pre-built binaries)
- Application code setup (Git clone or local)
- Backend and frontend configuration
- Database initialization
- Nginx web server configuration
- Systemd service creation
- Optional SSL/TLS setup with Let's Encrypt
- Optional firewall configuration

✅ **Interactive & Non-Interactive Modes**

- Interactive mode with prompts (recommended for first-time setup)
- Non-interactive mode for automation and CI/CD

✅ **Comprehensive Error Handling**

- Detailed logging to `/var/log/recipe-catalog-deployment.log`
- Color-coded console output
- Pre-flight system checks
- Service health verification

## Quick Start

### Interactive Deployment (Recommended)

The easiest way to deploy is using interactive mode:

```bash
# As root on your LXC container
cd /opt/recipe-catalog/scripts
sudo bash deploy-lxc.sh
```

The script will prompt you for:

- Server IP address or domain name
- Git repository URL (or use local files)
- SSL/TLS configuration (optional)
- SMTP email settings
- Firewall setup (optional)

### Non-Interactive Deployment

For automated deployments or CI/CD pipelines:

```bash
sudo bash deploy-lxc.sh \
    --non-interactive \
    --repo-url https://github.com/yourusername/recipe-catalog.git \
    --server-ip 192.168.1.100
```

### Using Existing Files

If you've already copied the application files to `/opt/recipe-catalog`:

```bash
sudo bash deploy-lxc.sh --repo-url local
```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--non-interactive` | Run without prompts (uses defaults) | `--non-interactive` |
| `--repo-url <url>` | Git repository URL or 'local' | `--repo-url https://github.com/user/repo.git` |
| `--server-ip <ip>` | Server IP address or domain | `--server-ip 192.168.1.100` |
| `--skip-python` | Skip Python 3.13 installation | `--skip-python` |
| `--help` | Show help message | `--help` |

## Prerequisites

Before running the deployment script:

1. **LXC Container Setup**
   - Create Debian 12.12-1 LXC container in Proxmox
   - Minimum specs:
     - 2 CPU cores
     - 2GB RAM (4GB recommended)
     - 8GB disk (16GB recommended)
   - Network configured with static IP or DHCP

2. **Access**
   - Root access to the container
   - Internet connection for downloading dependencies

3. **DNS (Optional, for SSL)**
   - Domain name pointed to your server IP
   - Required only if you want SSL/TLS certificates

## What The Script Does

### 1. System Preparation

- Updates all system packages
- Installs essential system dependencies (git, nginx, certbot, sqlite3)
- Installs Node.js 20.x and pnpm

### 2. Application Setup

- Creates `recipe-app` user for running the application
- Creates directory structure in `/opt/recipe-catalog`
- Clones repository or uses existing files
- Installs UV package manager for Python
- Installs Python 3.13 using UV (downloads pre-built binary, ~30 seconds)
- Pins the project to use Python 3.13
- Configures ENVIRONMENT=development for HTTP (required for cookies to work)

### 3. Backend Configuration

- Installs Python dependencies using UV
- Generates secure `.env` file with:
  - Random SECRET_KEY
  - Database configuration
  - CORS settings
  - Email/SMTP settings
  - Rate limiting
  - ENVIRONMENT=development (for HTTP deployments)
- Initializes SQLite database with migrations

### 4. Frontend Configuration

- Installs Node.js dependencies
- Generates `.env` file with API URL
- Builds production frontend bundle

### 5. Web Server Setup

- Configures Nginx as reverse proxy
- Sets up static file serving for frontend
- Proxies API requests to backend
- Adds security headers
- Optionally installs SSL certificate

### 6. Service Management

- Creates systemd service for backend
- Enables auto-start on boot
- Starts all services
- Verifies service health

### 7. Security (Optional)

- Configures UFW firewall
- Opens ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

## Post-Deployment

After successful deployment:

1. **Access the Application**

   ```text
   http://your-server-ip
   ```

2. **View API Documentation**

   ```text
   http://your-server-ip/api/docs
   ```

3. **Check Service Status**

   ```bash
   systemctl status recipe-catalog-backend
   systemctl status nginx
   ```

4. **View Logs**

   ```bash
   # Deployment log
   cat /var/log/recipe-catalog-deployment.log

   # Backend application logs
   journalctl -u recipe-catalog-backend -f

   # Nginx logs
   tail -f /var/log/nginx/recipe-catalog-error.log
   ```

5. **Register First User**
   - Navigate to the application in your browser
   - Click "Register" to create your account
   - Check email for verification (if SMTP configured)

## Troubleshooting

### Git Permission Errors During Update

If you see `error: insufficient permission for adding an object to repository database .git/objects`:

```bash
# Fix repository ownership (run as root)
chown -R recipe-app:recipe-app /opt/recipe-catalog

# Then retry the update
bash /opt/recipe-catalog/scripts/proxmox/update-app.sh
```

This happens if some git repository files were created by root instead of the `recipe-app` user. The update script now automatically fixes this, but you can run the command above manually if needed.

### Script Fails During Python Installation

If Python installation via UV fails:

```bash
# Check if UV is installed
su - recipe-app
~/.local/bin/uv --version

# Try installing Python manually
~/.local/bin/uv python install 3.13

# List installed Python versions
~/.local/bin/uv python list

# If still failing, check logs
cat /var/log/recipe-catalog-deployment.log
```

### Backend Service Won't Start

```bash
# Check the logs
journalctl -u recipe-catalog-backend -n 50

# Test backend manually
su - recipe-app
cd /opt/recipe-catalog/backend
~/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend Build Fails

```bash
# Check if pnpm is installed
pnpm --version

# Try building manually
su - recipe-app
cd /opt/recipe-catalog/frontend
pnpm install
pnpm build
```

### Can't Access Application

```bash
# Check if services are running
systemctl status recipe-catalog-backend
systemctl status nginx

# Check if ports are listening
ss -tulpn | grep -E ':(80|8000)'

# Check Nginx configuration
nginx -t

# Check firewall
ufw status
```

## Manual Configuration

After deployment, you may want to customize:

### Backend Environment Variables

Edit `/opt/recipe-catalog/backend/.env`:

```bash
sudo nano /opt/recipe-catalog/backend/.env
```

**Important Settings:**

- `ENVIRONMENT`: Set to `development` for HTTP or `production` for HTTPS
  - `development`: Allows cookies over HTTP (required for non-SSL deployments)
  - `production`: Requires HTTPS for secure cookies
- `ALLOWED_ORIGINS`: Must include your server IP/domain
- `SECRET_KEY`: Keep this secure and unique

After changes, restart the backend:

```bash
sudo systemctl restart recipe-catalog-backend
```

### Frontend Environment Variables

Edit `/opt/recipe-catalog/frontend/.env`:

```bash
sudo nano /opt/recipe-catalog/frontend/.env
```

After changes, rebuild and restart:

```bash
su - recipe-app
cd /opt/recipe-catalog/frontend
pnpm build
exit
sudo systemctl reload nginx
```

### Nginx Configuration

Edit `/etc/nginx/sites-available/recipe-catalog`:

```bash
sudo nano /etc/nginx/sites-available/recipe-catalog
```

Test and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Updating the Application

### Automated Update (Recommended)

Use the update script for safe, automated updates with automatic database backups:

```bash
# Standard update from git
sudo bash /opt/recipe-catalog/scripts/proxmox/update-app.sh

# Update from specific branch
sudo bash update-app.sh --branch develop

# Update without pulling from git (for local development)
sudo bash update-app.sh --skip-git

# Update without backup (not recommended)
sudo bash update-app.sh --skip-backup
```

**What the script does:**

1. **Backs up critical data:**
   - Creates timestamped database backup (keeps last 10)
   - Backs up backend and frontend `.env` files
2. Stops backend service
3. **Protects configuration files:**
   - Temporarily moves `.env` files before git operations
   - Pulls latest code from git
   - Restores `.env` files (preserves your settings)
4. Updates backend dependencies with UV
5. Runs database migrations
6. **Verifies database integrity** after migrations
7. Updates frontend dependencies
8. Builds frontend production bundle
9. Restarts services
10. Verifies service health

**Safety Features:**

- ✅ **`.env` files are never overwritten** - moved before git pull, restored after
- ✅ **Database backups** before any migrations
- ✅ **Database integrity checks** after migrations
- ✅ **Automatic rollback** if database corruption detected
- ✅ **Detailed rollback instructions** in case of issues
- ✅ **Service verification** before declaring success

**Script options:**

- `--skip-git`: Skip git pull (use for local development)
- `--skip-backup`: Skip database backup (not recommended)
- `--branch <name>`: Specify git branch (default: main)
- `--help`: Show usage information

**Features:**

- Automatic database backups in `/opt/recipe-catalog-backups/`
- **Preserves `.env` configuration files** (never overwritten)
- Database integrity verification after migrations
- Automatic rollback on database corruption
- Detailed logging to `/var/log/recipe-catalog-update.log`
- Service health verification
- Complete rollback instructions if issues occur

### Manual Update

To update manually (if you prefer step-by-step control):

```bash
# Stop services
sudo systemctl stop recipe-catalog-backend

# Update code (if using git)
cd /opt/recipe-catalog
sudo -u recipe-app git pull

# Update backend
cd backend
sudo -u recipe-app ~/.local/bin/uv sync
sudo -u recipe-app ~/.local/bin/uv run alembic upgrade head

# Update frontend
cd ../frontend
sudo -u recipe-app pnpm install
sudo -u recipe-app pnpm build

# Restart services
sudo systemctl start recipe-catalog-backend
sudo systemctl reload nginx
```

## Uninstalling

To completely remove Recipe Catalog:

```bash
# Stop and disable services
sudo systemctl stop recipe-catalog-backend
sudo systemctl disable recipe-catalog-backend
sudo rm /etc/systemd/system/recipe-catalog-backend.service
sudo systemctl daemon-reload

# Remove Nginx configuration
sudo rm /etc/nginx/sites-available/recipe-catalog
sudo rm /etc/nginx/sites-enabled/recipe-catalog
sudo systemctl reload nginx

# Remove application files
sudo rm -rf /opt/recipe-catalog

# Remove user
sudo userdel -r recipe-app

# Remove logs
sudo rm /var/log/recipe-catalog-deployment.log
sudo rm /var/log/nginx/recipe-catalog-*.log
```

## Support

For issues with the deployment script:

1. Check the deployment log: `/var/log/recipe-catalog-deployment.log`
2. Review the troubleshooting section above
3. Consult the main installation guide: `PROXMOX-LXC-INSTALL.md`
4. Check service logs with `journalctl`

## Script Version

Current version: **1.0.0**

## License

This script is part of the Recipe Catalog project.
