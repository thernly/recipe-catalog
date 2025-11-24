#!/bin/bash

#==============================================================================
# Recipe Catalog - Proxmox LXC Automated Deployment Script
#==============================================================================
# This script automates the deployment of Recipe Catalog on a Debian 12 LXC
# container. It handles system setup, dependency installation, application
# configuration, and service deployment.
#
# Usage:
#   bash deploy-lxc.sh [options]
#
# Options:
#   --non-interactive    Run without prompts (uses defaults)
#   --repo-url <url>     Git repository URL
#   --server-ip <ip>     Server IP address or domain
#   --skip-python        Skip Python 3.13 installation (if already installed)
#   --help               Show this help message
#
# Requirements:
#   - Debian 12 LXC container
#   - Root access
#   - Internet connection
#==============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

#==============================================================================
# Configuration Variables
#==============================================================================

SCRIPT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/recipe-catalog-deployment.log"
INSTALL_DIR="/opt/recipe-catalog"
APP_USER="recipe-app"
PYTHON_VERSION="3.13.0"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
NON_INTERACTIVE=false
SKIP_PYTHON=false
REPO_URL=""
SERVER_IP=""
USE_SSL=false
DOMAIN_NAME=""

#==============================================================================
# Helper Functions
#==============================================================================

log() {
    local message="$1"
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $message" | tee -a "$LOG_FILE"
}

log_error() {
    local message="$1"
    echo -e "${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE"
}

log_warn() {
    local message="$1"
    echo -e "${YELLOW}[WARN]${NC} $message" | tee -a "$LOG_FILE"
}

log_info() {
    local message="$1"
    echo -e "${BLUE}[INFO]${NC} $message" | tee -a "$LOG_FILE"
}

print_header() {
    local text="$1"
    echo ""
    echo "=============================================================================="
    echo "  $text"
    echo "=============================================================================="
    echo ""
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

check_os() {
    if [[ ! -f /etc/debian_version ]]; then
        log_error "This script is designed for Debian-based systems"
        exit 1
    fi

    local debian_version=$(cat /etc/debian_version | cut -d. -f1)
    if [[ "$debian_version" -lt 12 ]]; then
        log_warn "This script is optimized for Debian 12. Your version: $debian_version"
    fi
}

prompt_user() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"

    if [[ "$NON_INTERACTIVE" == true ]]; then
        eval "$var_name='$default'"
        return
    fi

    read -p "$prompt [$default]: " input
    eval "$var_name=\${input:-$default}"
}

show_help() {
    cat << EOF
Recipe Catalog - LXC Deployment Script v${SCRIPT_VERSION}

Usage: $(basename "$0") [options]

Options:
    --non-interactive       Run without prompts (uses defaults)
    --repo-url <url>        Git repository URL
    --server-ip <ip>        Server IP address or domain
    --skip-python           Skip Python 3.13 installation
    --help                  Show this help message

Examples:
    # Interactive mode (recommended)
    sudo bash $(basename "$0")

    # Non-interactive with custom settings
    sudo bash $(basename "$0") --non-interactive \\
        --repo-url https://github.com/user/repo.git \\
        --server-ip 192.168.1.100

EOF
    exit 0
}

#==============================================================================
# Parse Command Line Arguments
#==============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --non-interactive)
                NON_INTERACTIVE=true
                shift
                ;;
            --repo-url)
                REPO_URL="$2"
                shift 2
                ;;
            --server-ip)
                SERVER_IP="$2"
                shift 2
                ;;
            --skip-python)
                SKIP_PYTHON=true
                shift
                ;;
            --help)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                ;;
        esac
    done
}

#==============================================================================
# Interactive Configuration
#==============================================================================

gather_configuration() {
    print_header "Recipe Catalog Deployment Configuration"

    log_info "This script will install Recipe Catalog on this system."
    log_info "Please provide the following information:"
    echo ""

    # Get server IP
    if [[ -z "$SERVER_IP" ]]; then
        local detected_ip=$(hostname -I | awk '{print $1}')
        prompt_user "Enter server IP address or domain" "$detected_ip" SERVER_IP
    fi

    # Get repository URL
    if [[ -z "$REPO_URL" ]]; then
        prompt_user "Enter Git repository URL (or 'local' to use existing files)" "local" REPO_URL
    fi

    # SSL configuration
    if [[ "$NON_INTERACTIVE" == false ]]; then
        read -p "Do you want to configure SSL/TLS? (y/N): " ssl_choice
        if [[ "$ssl_choice" =~ ^[Yy]$ ]]; then
            USE_SSL=true
            prompt_user "Enter your domain name" "example.com" DOMAIN_NAME
        fi
    fi

    # Email configuration
    prompt_user "Enter SMTP host (for email notifications)" "smtp.gmail.com" SMTP_HOST
    prompt_user "Enter SMTP port" "587" SMTP_PORT
    prompt_user "Enter SMTP user (email address)" "your-email@gmail.com" SMTP_USER

    if [[ "$NON_INTERACTIVE" == false ]]; then
        read -s -p "Enter SMTP password: " SMTP_PASSWORD
        echo ""
    else
        SMTP_PASSWORD="change-this-password"
    fi

    echo ""
    log_info "Configuration complete. Starting deployment..."
    sleep 2
}

#==============================================================================
# Installation Steps
#==============================================================================

update_system() {
    print_header "Step 1: Updating System Packages"

    log "Updating package lists..."
    apt update >> "$LOG_FILE" 2>&1

    log "Upgrading installed packages..."
    apt upgrade -y >> "$LOG_FILE" 2>&1

    log "System update complete"
}

install_system_dependencies() {
    print_header "Step 2: Installing System Dependencies"

    log "Installing essential utilities..."
    apt install -y \
        curl \
        wget \
        git \
        nginx \
        certbot \
        python3-certbot-nginx \
        sqlite3 \
        >> "$LOG_FILE" 2>&1

    log "System dependencies installed"
}

install_nodejs() {
    print_header "Step 3: Installing Node.js and pnpm"

    if command -v node &> /dev/null; then
        local node_version=$(node --version)
        log_info "Node.js already installed: $node_version"
    else
        log "Installing Node.js 20.x..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >> "$LOG_FILE" 2>&1
        apt install -y nodejs >> "$LOG_FILE" 2>&1
        log "Node.js installed: $(node --version)"
    fi

    if command -v pnpm &> /dev/null; then
        log_info "pnpm already installed: $(pnpm --version)"
    else
        log "Installing pnpm..."
        npm install -g pnpm >> "$LOG_FILE" 2>&1
        log "pnpm installed: $(pnpm --version)"
    fi
}

install_python313() {
    if [[ "$SKIP_PYTHON" == true ]]; then
        log_info "Skipping Python 3.13 installation (--skip-python flag)"
        return
    fi

    print_header "Step 8: Installing Python 3.13 with UV"

    # Check if UV has Python 3.13 already installed
    if sudo -u "$APP_USER" test -f "/home/$APP_USER/.local/bin/uv" && \
       sudo -u "$APP_USER" /home/$APP_USER/.local/bin/uv python list 2>/dev/null | grep -q "3.13"; then
        log_info "Python 3.13 already installed via UV"
        return
    fi

    log "Installing Python 3.13 using UV (downloading pre-built binary)..."
    sudo -u "$APP_USER" /home/$APP_USER/.local/bin/uv python install 3.13 >> "$LOG_FILE" 2>&1

    log "Verifying Python 3.13 installation..."
    sudo -u "$APP_USER" /home/$APP_USER/.local/bin/uv python list >> "$LOG_FILE" 2>&1

    log "Python 3.13 installed successfully"
}

create_app_user() {
    print_header "Step 4: Creating Application User"

    if id "$APP_USER" &> /dev/null; then
        log_info "User $APP_USER already exists"
    else
        log "Creating user $APP_USER..."
        useradd -r -m -s /bin/bash "$APP_USER"
        log "User $APP_USER created"
    fi
}

create_directories() {
    print_header "Step 5: Creating Application Directories"

    log "Creating directory structure..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/backend/data"
    mkdir -p "$INSTALL_DIR/backend/logs"

    log "Setting directory permissions..."
    chown -R "$APP_USER:$APP_USER" "$INSTALL_DIR"

    log "Directories created"
}

setup_application_code() {
    print_header "Step 6: Setting Up Application Code"

    if [[ "$REPO_URL" == "local" ]]; then
        log_info "Using local files - ensure application code is in $INSTALL_DIR"

        if [[ ! -f "$INSTALL_DIR/backend/pyproject.toml" ]]; then
            log_error "Application code not found in $INSTALL_DIR"
            log_error "Please copy your application files to $INSTALL_DIR and run again"
            exit 1
        fi
    else
        log "Cloning repository from $REPO_URL..."

        if [[ -d "$INSTALL_DIR/.git" ]]; then
            log_info "Repository already cloned, pulling latest changes..."
            cd "$INSTALL_DIR"
            sudo -u "$APP_USER" git pull >> "$LOG_FILE" 2>&1
        else
            rm -rf "$INSTALL_DIR"
            mkdir -p "$INSTALL_DIR"
            sudo -u "$APP_USER" git clone "$REPO_URL" "$INSTALL_DIR" >> "$LOG_FILE" 2>&1
        fi
    fi

    chown -R "$APP_USER:$APP_USER" "$INSTALL_DIR"
    log "Application code ready"
}

install_uv() {
    print_header "Step 7: Installing UV Package Manager"

    if sudo -u "$APP_USER" test -f "/home/$APP_USER/.local/bin/uv"; then
        log_info "UV already installed for $APP_USER"
    else
        log "Installing UV as $APP_USER..."
        sudo -u "$APP_USER" bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh" >> "$LOG_FILE" 2>&1
        log "UV installed: $(sudo -u "$APP_USER" /home/$APP_USER/.local/bin/uv --version)"
    fi
}

setup_backend() {
    print_header "Step 9: Setting Up Backend"

    cd "$INSTALL_DIR/backend"

    log "Pinning Python 3.13 for the project..."
    sudo -u "$APP_USER" bash -c "cd $INSTALL_DIR/backend && /home/$APP_USER/.local/bin/uv python pin 3.13" >> "$LOG_FILE" 2>&1

    log "Installing backend dependencies..."
    sudo -u "$APP_USER" bash -c "cd $INSTALL_DIR/backend && /home/$APP_USER/.local/bin/uv sync" >> "$LOG_FILE" 2>&1

    log "Generating environment configuration..."
    local secret_key=$(openssl rand -hex 32)

    cat > "$INSTALL_DIR/backend/.env" << EOF
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./data/recipes.db

# Security
SECRET_KEY=$secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (comma-separated list)
ALLOWED_ORIGINS=http://localhost,http://${SERVER_IP}
ALLOWED_METHODS=GET,POST,PUT,DELETE,PATCH
ALLOWED_HEADERS=Authorization,Content-Type,Accept,X-CSRF-Token

# Email Configuration (SMTP)
SMTP_HOST=${SMTP_HOST}
SMTP_PORT=${SMTP_PORT}
SMTP_USER=${SMTP_USER}
SMTP_PASSWORD=${SMTP_PASSWORD}
FROM_EMAIL=noreply@recipecatalog.app
FROM_NAME=Recipe Catalog

# Application Settings
APP_NAME=Recipe Catalog
FRONTEND_URL=http://${SERVER_IP}
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

    chown "$APP_USER:$APP_USER" "$INSTALL_DIR/backend/.env"
    chmod 600 "$INSTALL_DIR/backend/.env"

    log "Initializing database..."
    sudo -u "$APP_USER" bash -c "cd $INSTALL_DIR/backend && /home/$APP_USER/.local/bin/uv run alembic upgrade head" >> "$LOG_FILE" 2>&1

    log "Backend setup complete"
}

setup_frontend() {
    print_header "Step 10: Setting Up Frontend"

    cd "$INSTALL_DIR/frontend"

    log "Installing frontend dependencies..."
    sudo -u "$APP_USER" bash -c "cd $INSTALL_DIR/frontend && pnpm install" >> "$LOG_FILE" 2>&1

    log "Generating frontend environment configuration..."
    local api_url="http://${SERVER_IP}/api"
    if [[ "$USE_SSL" == true ]]; then
        api_url="https://${DOMAIN_NAME}/api"
    fi

    cat > "$INSTALL_DIR/frontend/.env" << EOF
VITE_API_URL=${api_url}
VITE_APP_NAME=Recipe Catalog
EOF

    chown "$APP_USER:$APP_USER" "$INSTALL_DIR/frontend/.env"

    log "Building frontend for production..."
    sudo -u "$APP_USER" bash -c "cd $INSTALL_DIR/frontend && pnpm build" >> "$LOG_FILE" 2>&1

    log "Frontend setup complete"
}

configure_nginx() {
    print_header "Step 11: Configuring Nginx"

    log "Creating Nginx configuration..."

    local server_name="_"
    if [[ "$USE_SSL" == true ]]; then
        server_name="$DOMAIN_NAME www.$DOMAIN_NAME"
    fi

    cat > /etc/nginx/sites-available/recipe-catalog << EOF
server {
    listen 80;
    server_name $server_name;

    # Frontend static files
    location / {
        root $INSTALL_DIR/frontend/build;
        try_files \$uri \$uri/ /index.html;

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
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

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

    log "Enabling site..."
    ln -sf /etc/nginx/sites-available/recipe-catalog /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    log "Testing Nginx configuration..."
    nginx -t >> "$LOG_FILE" 2>&1

    log "Nginx configured"
}

setup_ssl() {
    if [[ "$USE_SSL" != true ]]; then
        return
    fi

    print_header "Step 12: Setting Up SSL/TLS"

    log "Configuring Let's Encrypt certificate..."
    certbot --nginx -d "$DOMAIN_NAME" -d "www.$DOMAIN_NAME" --non-interactive --agree-tos --email "$SMTP_USER" >> "$LOG_FILE" 2>&1

    log "SSL certificate installed"
}

create_systemd_service() {
    print_header "Step 13: Creating Systemd Service"

    log "Creating backend service..."

    cat > /etc/systemd/system/recipe-catalog-backend.service << EOF
[Unit]
Description=Recipe Catalog Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=/home/$APP_USER/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

# Start command using UV
ExecStart=/home/$APP_USER/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4

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
ReadWritePaths=$INSTALL_DIR/backend

[Install]
WantedBy=multi-user.target
EOF

    log "Reloading systemd daemon..."
    systemctl daemon-reload

    log "Systemd service created"
}

start_services() {
    print_header "Step 14: Starting Services"

    log "Enabling and starting backend service..."
    systemctl enable recipe-catalog-backend >> "$LOG_FILE" 2>&1
    systemctl start recipe-catalog-backend

    log "Enabling and starting Nginx..."
    systemctl enable nginx >> "$LOG_FILE" 2>&1
    systemctl restart nginx

    sleep 3

    log "Checking service status..."
    if systemctl is-active --quiet recipe-catalog-backend; then
        log "✓ Backend service is running"
    else
        log_error "✗ Backend service failed to start"
        log_error "Check logs with: journalctl -u recipe-catalog-backend -n 50"
    fi

    if systemctl is-active --quiet nginx; then
        log "✓ Nginx is running"
    else
        log_error "✗ Nginx failed to start"
        log_error "Check logs with: journalctl -u nginx -n 50"
    fi
}

configure_firewall() {
    print_header "Step 15: Configuring Firewall (Optional)"

    if [[ "$NON_INTERACTIVE" == false ]]; then
        read -p "Do you want to configure UFW firewall? (y/N): " firewall_choice
        if [[ ! "$firewall_choice" =~ ^[Yy]$ ]]; then
            log_info "Skipping firewall configuration"
            return
        fi
    else
        log_info "Skipping firewall configuration in non-interactive mode"
        return
    fi

    log "Installing and configuring UFW..."
    apt install -y ufw >> "$LOG_FILE" 2>&1

    ufw allow 22/tcp >> "$LOG_FILE" 2>&1
    ufw allow 80/tcp >> "$LOG_FILE" 2>&1
    ufw allow 443/tcp >> "$LOG_FILE" 2>&1

    echo "y" | ufw enable >> "$LOG_FILE" 2>&1

    log "Firewall configured"
}

print_summary() {
    print_header "Deployment Complete!"

    echo ""
    log "Recipe Catalog has been successfully deployed!"
    echo ""
    log_info "Access your application:"
    if [[ "$USE_SSL" == true ]]; then
        log_info "  • Frontend: https://${DOMAIN_NAME}"
        log_info "  • API Docs: https://${DOMAIN_NAME}/api/docs"
    else
        log_info "  • Frontend: http://${SERVER_IP}"
        log_info "  • API Docs: http://${SERVER_IP}/api/docs"
    fi
    echo ""
    log_info "Service Management:"
    log_info "  • Backend status:  systemctl status recipe-catalog-backend"
    log_info "  • Backend logs:    journalctl -u recipe-catalog-backend -f"
    log_info "  • Nginx status:    systemctl status nginx"
    log_info "  • Nginx logs:      tail -f /var/log/nginx/recipe-catalog-*.log"
    echo ""
    log_info "Next Steps:"
    log_info "  1. Open your browser and navigate to the application URL"
    log_info "  2. Register your first user account"
    log_info "  3. Configure email settings in $INSTALL_DIR/backend/.env if needed"
    log_info "  4. Review logs to ensure everything is working correctly"
    echo ""
    log_info "Full deployment log saved to: $LOG_FILE"
    echo ""
    log "Thank you for using Recipe Catalog!"
    echo ""
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    # Initialize log file
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"

    # Print banner
    clear
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║          Recipe Catalog - LXC Deployment Automation Script           ║
║                         Version 1.0.0                                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF

    # Pre-flight checks
    check_root
    check_os

    # Parse arguments
    parse_args "$@"

    # Gather configuration
    gather_configuration

    # Execute installation steps
    update_system
    install_system_dependencies
    install_nodejs
    create_app_user
    create_directories
    setup_application_code
    install_uv
    install_python313
    setup_backend
    setup_frontend
    configure_nginx
    setup_ssl
    create_systemd_service
    start_services
    configure_firewall

    # Print summary
    print_summary
}

# Run main function
main "$@"
