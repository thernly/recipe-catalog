# Recipe Catalog - Proxmox LXC Installation Guide

This guide walks you through installing the Recipe Catalog application on a Debian 12.12-1 LXC container running on Proxmox.

## 🚀 Quick Start with Automation Script

**NEW:** We now provide a fully automated deployment script that handles the entire installation process!

```bash
# Download and run the automated deployment script
cd /tmp
wget https://raw.githubusercontent.com/thernly/recipe-catalog/main/scripts/deploy-lxc.sh
chmod +x deploy-lxc.sh
sudo bash deploy-lxc.sh
```

The automation script will:

- ✅ Install all system dependencies
- ✅ Install Python 3.13 using UV (pre-built binaries)
- ✅ Set up backend and frontend
- ✅ Configure Nginx and systemd services
- ✅ Initialize the database
- ✅ Optionally set up SSL/TLS

See [`scripts/README.md`](../../scripts/README.md) for detailed automation script documentation.

---

## Manual Installation

If you prefer to install manually or want to understand each step, continue with this guide below.

## Table of Contents

- [Prerequisites](#prerequisites)
- [LXC Container Setup](#lxc-container-setup)
- [System Preparation](#system-preparation)
- [Backend Installation](#backend-installation)
- [Frontend Installation](#frontend-installation)
- [Nginx Configuration](#nginx-configuration)
- [SSL/TLS Setup (Optional)](#ssltls-setup-optional)
- [Systemd Service Configuration](#systemd-service-configuration)
- [Email Configuration](#email-configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Proxmox VE installed and running
- Access to Proxmox web interface or SSH
- Basic understanding of Linux command line
- (Optional) Domain name for SSL certificate

---

## LXC Container Setup

### 1. Create LXC Container in Proxmox

1. In Proxmox web interface, click **Create CT**
2. Configure the container:
   - **Hostname**: `recipe-catalog` (or your preference)
   - **Password**: Set a strong root password
   - **Template**: `debian-12.12-1-standard`
   - **Disk Size**: 8GB minimum (16GB recommended)
   - **CPU Cores**: 2 cores minimum
   - **Memory**: 2048MB minimum (4096MB recommended)
   - **Network**: Bridge mode with static IP or DHCP
   - **Start at boot**: ✓ Enabled

3. Click **Finish** and start the container

### 2. Access the Container

```bash
# From Proxmox host, enter the container
pct enter <container-id>

# Or via SSH
ssh root@<container-ip>
```

---

## System Preparation

### 1. Update System Packages

```bash
apt update && apt upgrade -y
```

### 2. Install Required System Dependencies

```bash
# Install essential build tools and utilities
apt install -y \
    curl \
    wget \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    sqlite3

# Install Node.js 20.x (required for frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Install pnpm package manager
npm install -g pnpm
```

### 3. Create Application User

```bash
# Create dedicated user for running the application
useradd -r -m -s /bin/bash recipe-app
```

### 4. Create Application Directories

```bash
# Create directory structure
mkdir -p /opt/recipe-catalog
mkdir -p /opt/recipe-catalog/backend/data
mkdir -p /opt/recipe-catalog/backend/logs
chown -R recipe-app:recipe-app /opt/recipe-catalog
```

---

## Backend Installation

### 1. Clone Repository or Upload Code

```bash
# Option A: Clone from Git (if hosted)
cd /opt/recipe-catalog
git clone <your-repo-url> .

# Option B: Upload code manually
# Use SCP or SFTP to upload your code to /opt/recipe-catalog
```

### 2. Install UV Package Manager and Python 3.13

Debian 12 ships with Python 3.11, but this application requires Python 3.13. We'll use UV to manage Python versions - it downloads pre-built binaries, which is much faster than compiling from source.

```bash
# Install UV as the recipe-app user
su - recipe-app -c "curl -LsSf https://astral.sh/uv/install.sh | sh"

# Verify UV installation
su - recipe-app -c "~/.local/bin/uv --version"

# Install Python 3.13 using UV (downloads pre-built binary, ~30 seconds)
su - recipe-app -c "~/.local/bin/uv python install 3.13"

# Pin the project to use Python 3.13
su - recipe-app -c "cd /opt/recipe-catalog/backend && ~/.local/bin/uv python pin 3.13"

# Verify Python installation
su - recipe-app -c "~/.local/bin/uv python list"
```

### 3. Setup Backend Environment

```bash
cd /opt/recipe-catalog/backend

# Create Python virtual environment and install dependencies
su - recipe-app -c "cd /opt/recipe-catalog/backend && ~/.local/bin/uv sync"
```

### 4. Configure Backend Environment Variables

```bash
# Generate a secure secret key
SECRET_KEY=$(openssl rand -hex 32)

# Create .env file
cat > /opt/recipe-catalog/backend/.env << EOF
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./data/recipes.db

# Security
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (comma-separated list)
ALLOWED_ORIGINS=http://localhost,http://<your-server-ip>
ALLOWED_METHODS=GET,POST,PUT,DELETE,PATCH
ALLOWED_HEADERS=Authorization,Content-Type,Accept,X-CSRF-Token

# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@recipecatalog.app
FROM_NAME=Recipe Catalog

# Application Settings
APP_NAME=Recipe Catalog
FRONTEND_URL=http://<your-server-ip>
ENVIRONMENT=production
DEBUG=False

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# File Upload
MAX_UPLOAD_SIZE_MB=10
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/webp

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF

# Set proper permissions
chown recipe-app:recipe-app /opt/recipe-catalog/backend/.env
chmod 600 /opt/recipe-catalog/backend/.env
```

**Important**: Edit the `.env` file to replace placeholder values:

- `<your-server-ip>`: Your container's IP address or domain
- Email settings: Configure with your SMTP provider (see [Email Configuration](#email-configuration) section)

### 5. Initialize Database

```bash
cd /opt/recipe-catalog/backend

# Run database migrations as recipe-app user
su - recipe-app -c "cd /opt/recipe-catalog/backend && ~/.local/bin/uv run alembic upgrade head"
```

### 6. Verify Backend Installation

```bash
# Test backend startup
su - recipe-app -c "cd /opt/recipe-catalog/backend && ~/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"

# Press Ctrl+C after verifying it starts without errors
```

---

## Frontend Installation

### 1. Install Frontend Dependencies

```bash
cd /opt/recipe-catalog/frontend

# Install dependencies as recipe-app user
su - recipe-app -c "cd /opt/recipe-catalog/frontend && pnpm install"
```

### 2. Configure Frontend Environment

```bash
# Create .env file
cat > /opt/recipe-catalog/frontend/.env << 'EOF'
VITE_API_URL=http://<your-server-ip>/api
VITE_APP_NAME=Recipe Catalog
EOF

# Replace <your-server-ip> with your actual IP or domain
# Example: VITE_API_URL=http://192.168.1.100/api
# For production with domain: VITE_API_URL=https://yourdomain.com/api

# Set proper permissions
chown recipe-app:recipe-app /opt/recipe-catalog/frontend/.env
```

### 3. Build Frontend for Production

```bash
# Build the frontend as recipe-app user
su - recipe-app -c "cd /opt/recipe-catalog/frontend && pnpm build"
```

The built files will be in `/opt/recipe-catalog/frontend/build/`

---

## Nginx Configuration

### 1. Create Nginx Configuration

```bash
cat > /etc/nginx/sites-available/recipe-catalog << 'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain name if you have one

    # Frontend static files
    location / {
        root /opt/recipe-catalog/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API proxy
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/recipe-catalog-access.log;
    error_log /var/log/nginx/recipe-catalog-error.log;
}
EOF
```

### 2. Enable Site and Test Configuration

```bash
# Create symlink to enable site
ln -s /etc/nginx/sites-available/recipe-catalog /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test configuration
nginx -t

# Reload Nginx
systemctl reload nginx
```

---

## SSL/TLS Setup (Optional)

If you have a domain name pointed to your server:

```bash
# Install SSL certificate with Let's Encrypt
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Certbot will automatically modify your Nginx configuration
# and set up automatic renewal
```

For self-signed certificate (development/internal use):

```bash
# Generate self-signed certificate
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/recipe-catalog.key \
    -out /etc/nginx/ssl/recipe-catalog.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=recipe-catalog"

# Update Nginx configuration to use SSL
# Add these lines to your server block:
#   listen 443 ssl;
#   ssl_certificate /etc/nginx/ssl/recipe-catalog.crt;
#   ssl_certificate_key /etc/nginx/ssl/recipe-catalog.key;
```

---

## Systemd Service Configuration

### 1. Create Backend Service

```bash
cat > /etc/systemd/system/recipe-catalog-backend.service << 'EOF'
[Unit]
Description=Recipe Catalog Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=recipe-app
Group=recipe-app
WorkingDirectory=/opt/recipe-catalog/backend
Environment="PATH=/home/recipe-app/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

# Start command using UV
ExecStart=/home/recipe-app/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=recipe-catalog-backend

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/recipe-catalog/backend

[Install]
WantedBy=multi-user.target
EOF
```

### 2. Enable and Start Services

```bash
# Reload systemd daemon
systemctl daemon-reload

# Enable backend service to start on boot
systemctl enable recipe-catalog-backend

# Start backend service
systemctl start recipe-catalog-backend

# Enable Nginx to start on boot
systemctl enable nginx

# Check service status
systemctl status recipe-catalog-backend
systemctl status nginx
```

### 3. Verify Auto-Startup

```bash
# Test by rebooting the container
reboot

# After reboot, check services
systemctl status recipe-catalog-backend
systemctl status nginx
```

---

## Email Configuration

### 1. Gmail SMTP Setup (Example)

If using Gmail for email notifications:

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account Settings → Security
   - Select "2-Step Verification"
   - Select "App passwords"
   - Generate a new app password for "Mail"
3. Update `/opt/recipe-catalog/backend/.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM=your-email@gmail.com
```

### 2. Alternative SMTP Providers

**SendGrid:**

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

**Mailgun:**

```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-password
```

### 3. Restart Backend After Email Configuration

```bash
systemctl restart recipe-catalog-backend
```

---

## Verification

### 1. Check Service Status

```bash
# Backend status
systemctl status recipe-catalog-backend

# Nginx status
systemctl status nginx

# View backend logs
journalctl -u recipe-catalog-backend -f
```

### 2. Test HTTP Access

```bash
# From the container
curl http://localhost/
curl http://localhost/api/docs

# From your browser
http://<container-ip>/
http://<container-ip>/api/docs
```

### 3. Register First User

1. Open `http://<container-ip>` in your browser
2. Click "Register" or navigate to `/auth/register`
3. Create your first user account
4. Check your email for verification link

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
journalctl -u recipe-catalog-backend -n 50

# Check if port is in use
netstat -tulpn | grep 8000

# Test manually
su - recipe-app
cd /opt/recipe-catalog/backend
~/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Nginx Errors

```bash
# Check Nginx configuration
nginx -t

# View error logs
tail -f /var/log/nginx/recipe-catalog-error.log

# Check if Nginx is running
systemctl status nginx
```

### Database Issues

```bash
# Check database file permissions
ls -la /opt/recipe-catalog/backend/data/recipes.db

# Ensure recipe-app owns the file
chown recipe-app:recipe-app /opt/recipe-catalog/backend/data/recipes.db

# Check database integrity
su - recipe-app -c "cd /opt/recipe-catalog/backend && sqlite3 data/recipes.db 'PRAGMA integrity_check;'"
```

### Email Not Sending

```bash
# Test SMTP connection
telnet smtp.gmail.com 587

# Check backend logs for email errors
journalctl -u recipe-catalog-backend | grep -i email

# Verify .env file has correct SMTP settings
cat /opt/recipe-catalog/backend/.env | grep SMTP
```

### Permission Issues

```bash
# Fix ownership of all application files
chown -R recipe-app:recipe-app /opt/recipe-catalog

# Fix .env permissions
chmod 600 /opt/recipe-catalog/backend/.env
```

### Container Won't Auto-Start

```bash
# Check if services are enabled
systemctl is-enabled recipe-catalog-backend
systemctl is-enabled nginx

# Enable if needed
systemctl enable recipe-catalog-backend
systemctl enable nginx

# Check Proxmox container settings
# Ensure "Start at boot" is checked in Proxmox web UI
```

---

## Maintenance Tasks

### Backup Database

```bash
# Create backup directory
mkdir -p /opt/backups

# Backup database
cp /opt/recipe-catalog/backend/data/recipes.db \
   /opt/backups/recipes-$(date +%Y%m%d-%H%M%S).db

# Automated backup script
cat > /usr/local/bin/backup-recipe-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DB_FILE="/opt/recipe-catalog/backend/data/recipes.db"
mkdir -p $BACKUP_DIR
cp $DB_FILE $BACKUP_DIR/recipes-$(date +%Y%m%d-%H%M%S).db
# Keep only last 30 days of backups
find $BACKUP_DIR -name "recipes-*.db" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup-recipe-db.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/backup-recipe-db.sh" | crontab -
```

### Update Application

```bash
# Stop backend service
systemctl stop recipe-catalog-backend

# Pull latest code (if using git)
cd /opt/recipe-catalog
git pull

# Update backend dependencies
su - recipe-app -c "cd /opt/recipe-catalog/backend && uv sync"

# Run database migrations
su - recipe-app -c "cd /opt/recipe-catalog/backend && uv run alembic upgrade head"

# Rebuild frontend
su - recipe-app -c "cd /opt/recipe-catalog/frontend && pnpm install && pnpm build"

# Restart services
systemctl start recipe-catalog-backend
systemctl reload nginx
```

### View Logs

```bash
# Backend logs (real-time)
journalctl -u recipe-catalog-backend -f

# Backend logs (last 100 lines)
journalctl -u recipe-catalog-backend -n 100

# Nginx access logs
tail -f /var/log/nginx/recipe-catalog-access.log

# Nginx error logs
tail -f /var/log/nginx/recipe-catalog-error.log
```

---

## Security Recommendations

1. **Firewall**: Configure firewall to only allow necessary ports

   ```bash
   apt install ufw
   ufw allow 22/tcp   # SSH
   ufw allow 80/tcp   # HTTP
   ufw allow 443/tcp  # HTTPS
   ufw enable
   ```

2. **Fail2Ban**: Protect against brute-force attacks

   ```bash
   apt install fail2ban
   systemctl enable fail2ban
   ```

3. **Regular Updates**: Keep system updated

   ```bash
   apt update && apt upgrade -y
   ```

4. **SSH Hardening**: Disable root login, use SSH keys

   ```bash
   # Edit /etc/ssh/sshd_config
   PermitRootLogin no
   PasswordAuthentication no
   ```

5. **Database Backups**: Implement automated backups (see Maintenance section)

6. **SSL/TLS**: Use Let's Encrypt certificates for production

---

## Performance Tuning

### Backend Workers

Adjust workers based on CPU cores:

```bash
# In /etc/systemd/system/recipe-catalog-backend.service
ExecStart=/home/recipe-app/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4

# Rule of thumb: (2 x CPU cores) + 1
# For 2 cores: --workers 5
```

### Nginx Caching

Add to Nginx configuration:

```nginx
# In /etc/nginx/sites-available/recipe-catalog
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=recipe_cache:10m max_size=100m;

location /api {
    proxy_cache recipe_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_use_stale error timeout http_500 http_502 http_503 http_504;
    # ... rest of proxy settings
}
```

---

## Support

For application issues, check:

- Project documentation in `/opt/recipe-catalog/docs/`
- API documentation at `http://<your-ip>/api/docs`
- Backend logs: `journalctl -u recipe-catalog-backend`
- Nginx logs: `/var/log/nginx/recipe-catalog-*.log`

---

**Installation Guide Version**: 1.0  
**Last Updated**: November 23, 2025  
**Target OS**: Debian 12.12-1 (LXC Container)  
**Tested on**: Proxmox VE 8.x
