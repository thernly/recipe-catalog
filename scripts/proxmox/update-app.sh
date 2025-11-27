#!/bin/bash

#===============================================================================
# Recipe Catalog - Application Update Script
#===============================================================================
# This script automates the process of updating the Recipe Catalog application
# to the latest version on a Proxmox LXC container running Debian 12.
#
# Usage:
#   sudo bash update-app.sh [OPTIONS]
#
# Options:
#   --skip-git          Skip git pull (for local development)
#   --skip-backup       Skip database backup before update
#   --branch <name>     Git branch to pull from (default: main)
#   --help              Show this help message
#
# Requirements:
#   - Must be run as root or with sudo
#   - Application must be installed at /opt/recipe-catalog
#   - Services must be managed by systemd
#
# Version: 1.0.0
#===============================================================================

set -e  # Exit on error
# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/recipe-catalog"
APP_USER="recipe-app"
BACKEND_SERVICE="recipe-catalog-backend"
DATA_DIR="/opt/recipe-catalog/backend/data"
NGINX_SERVICE="nginx"
LOG_FILE="/var/log/recipe-catalog-update.log"
BACKUP_DIR="/opt/recipe-catalog-backups"
GIT_BRANCH="main"
SKIP_GIT=false
SKIP_BACKUP=false

#===============================================================================
# Utility Functions
#===============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
    echo "[SUCCESS] $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    echo "[ERROR] $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    echo "[WARNING] $1" >> "$LOG_FILE"
}

error_exit() {
    log_error "$1"
    log_error "Update failed! Check log: $LOG_FILE"
    exit 1
}

show_help() {
    cat << EOF
Recipe Catalog - Application Update Script

Usage:
    sudo bash update-app.sh [OPTIONS]

Options:
    --skip-git          Skip git pull (for local development)
    --skip-backup       Skip database backup before update
    --branch <name>     Git branch to pull from (default: main)
    --help              Show this help message

Examples:
    # Standard update from git
    bash update-app.sh

    # Update from specific branch
    bash update-app.sh --branch develop

    # Update without pulling from git (local changes)
    bash update-app.sh --skip-git

    # Update without backup (not recommended)
    bash update-app.sh --skip-backup

For more information, see: scripts/proxmox/README.md

EOF
    exit 0
}
#===============================================================================
# Argument Parsing
#===============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-git)
            SKIP_GIT=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --branch)
            GIT_BRANCH="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

#===============================================================================
# Pre-Flight Checks
#===============================================================================

log "=== Recipe Catalog Update Script v1.0.0 ==="
log "Starting update process..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error_exit "This script must be run as root or with sudo"
fi

# Check if application directory exists
if [[ ! -d "$APP_DIR" ]]; then
    error_exit "Application directory not found: $APP_DIR"
fi

# Check if recipe-app user exists
if ! id "$APP_USER" &>/dev/null; then
    error_exit "User $APP_USER does not exist"
fi

# Check if backend service exists
if ! systemctl list-unit-files | grep -q "$BACKEND_SERVICE"; then
    error_exit "Backend service not found: $BACKEND_SERVICE"
fi

log_success "Pre-flight checks passed"

#===============================================================================
# Backup Critical Files
#===============================================================================

if [[ "$SKIP_BACKUP" == false ]]; then
    log "Creating backups..."
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    chown "$APP_USER:$APP_USER" "$BACKUP_DIR"
    
    # Backup database with timestamp
    TIMESTAMP=$(date +'%Y%m%d-%H%M%S')
    BACKUP_FILE="$BACKUP_DIR/recipes-$TIMESTAMP.db"
    
    if [[ -f "$DATA_DIR/recipes.db" ]]; then
        cp "$DATA_DIR/recipes.db" "$BACKUP_FILE" || error_exit "Database backup failed"
        chown "$APP_USER:$APP_USER" "$BACKUP_FILE"
        log_success "Database backed up to: $BACKUP_FILE"
        
        # Keep only last 10 backups
        cd "$BACKUP_DIR"
        ls -t recipes-*.db | tail -n +11 | xargs -r rm
        log "Kept last 10 backups, removed older ones"
    else
        log_warning "Database file not found, skipping backup"
    fi
    
    # Backup .env files (always preserve user configuration)
    log "Backing up configuration files..."
    if [[ -f "$APP_DIR/backend/.env" ]]; then
        cp "$APP_DIR/backend/.env" "$BACKUP_DIR/backend-env-$TIMESTAMP" || log_warning "Failed to backup backend .env"
        log_success "Backend .env backed up"
    fi
    if [[ -f "$APP_DIR/frontend/.env" ]]; then
        cp "$APP_DIR/frontend/.env" "$BACKUP_DIR/frontend-env-$TIMESTAMP" || log_warning "Failed to backup frontend .env"
        log_success "Frontend .env backed up"
    fi
else
    log_warning "Skipping backups (--skip-backup flag)"
fi

#===============================================================================
# Stop Services
#===============================================================================

log "Stopping backend service..."
systemctl stop "$BACKEND_SERVICE" || error_exit "Failed to stop backend service"
log_success "Backend service stopped"

#===============================================================================
# Update Code
#===============================================================================

if [[ "$SKIP_GIT" == false ]]; then
    log "Updating code from git (branch: $GIT_BRANCH)..."
    
    cd "$APP_DIR"
    
    # Check if it's a git repository
    if [[ ! -d ".git" ]]; then
        log_warning "Not a git repository, skipping git pull"
    else
        # Preserve .env files by temporarily moving them
        log "Protecting configuration files from git operations..."
        TEMP_ENV_DIR=$(mktemp -d)
        
        if [[ -f "$APP_DIR/backend/.env" ]]; then
            mv "$APP_DIR/backend/.env" "$TEMP_ENV_DIR/backend.env" || log_warning "Could not move backend .env"
        fi
        if [[ -f "$APP_DIR/frontend/.env" ]]; then
            mv "$APP_DIR/frontend/.env" "$TEMP_ENV_DIR/frontend.env" || log_warning "Could not move frontend .env"
        fi
        
        # Stash any other local changes (won't affect .env since we moved them)
        su -s /bin/bash "$APP_USER" -c "cd $APP_DIR && git stash save 'Auto-stash before update $(date +'%Y-%m-%d %H:%M:%S')'"
        
        # Pull latest changes
        su -s /bin/bash "$APP_USER" -c "cd $APP_DIR && git checkout $GIT_BRANCH" || error_exit "Failed to checkout branch: $GIT_BRANCH"
        su -s /bin/bash "$APP_USER" -c "cd $APP_DIR && git pull origin $GIT_BRANCH" || error_exit "Failed to pull from git"
        
        # Restore .env files
        log "Restoring configuration files..."
        if [[ -f "$TEMP_ENV_DIR/backend.env" ]]; then
            mv "$TEMP_ENV_DIR/backend.env" "$APP_DIR/backend/.env" || error_exit "Failed to restore backend .env"
            chown "$APP_USER:$APP_USER" "$APP_DIR/backend/.env"
            log_success "Backend .env restored"
        fi
        if [[ -f "$TEMP_ENV_DIR/frontend.env" ]]; then
            mv "$TEMP_ENV_DIR/frontend.env" "$APP_DIR/frontend/.env" || error_exit "Failed to restore frontend .env"
            chown "$APP_USER:$APP_USER" "$APP_DIR/frontend/.env"
            log_success "Frontend .env restored"
        fi
        
        # Clean up temp directory
        rm -rf "$TEMP_ENV_DIR"
        
        log_success "Code updated from git (configuration files preserved)"
    fi
else
    log_warning "Skipping git pull (--skip-git flag)"
fi

#===============================================================================
# Update Backend
#===============================================================================

log "Updating backend dependencies..."

cd "$APP_DIR/backend"

# Check if UV is installed
if [[ ! -f "/home/$APP_USER/.local/bin/uv" ]]; then
    error_exit "UV package manager not found for user $APP_USER"
fi

# Sync dependencies
su -s /bin/bash "$APP_USER" -c "cd $APP_DIR/backend && /home/$APP_USER/.local/bin/uv sync" || error_exit "Failed to sync backend dependencies"
log_success "Backend dependencies updated"

# Run database migrations
log "Running database migrations..."
su -s /bin/bash "$APP_USER" -c "cd $APP_DIR/backend && /home/$APP_USER/.local/bin/uv run alembic upgrade head" || error_exit "Database migration failed"
log_success "Database migrations completed"

# Verify database integrity after migration
log "Verifying database integrity..."
if command -v sqlite3 &> /dev/null && [[ -f "$DATA_DIR/recipes.db" ]]; then
    if sqlite3 "$DATA_DIR/recipes.db" "PRAGMA integrity_check;" | grep -q "ok"; then
        log_success "Database integrity check passed"
    else
        log_error "Database integrity check failed!"
        log_error "Restoring from backup: $BACKUP_FILE"
        if [[ -f "$BACKUP_FILE" ]]; then
            cp "$BACKUP_FILE" "$DATA_DIR/recipes.db"
            error_exit "Database corrupted - restored from backup. Migration may need manual intervention."
        else
            error_exit "Database corrupted and no backup available!"
        fi
    fi
else
    log_warning "Unable to verify database integrity (sqlite3 not available or db not found)"
fi

#===============================================================================
# Update Frontend
#===============================================================================

log "Updating frontend dependencies..."

cd "$APP_DIR/frontend"

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    error_exit "pnpm not found"
fi

# Install dependencies
su -s /bin/bash "$APP_USER" -c "cd $APP_DIR/frontend && pnpm install" || error_exit "Failed to install frontend dependencies"
log_success "Frontend dependencies updated"

# Build frontend
log "Building frontend..."
su -s /bin/bash "$APP_USER" -c "cd $APP_DIR/frontend && pnpm build" || error_exit "Frontend build failed"
log_success "Frontend build completed"

#===============================================================================
# Restart Services
#===============================================================================

log "Starting backend service..."
systemctl start "$BACKEND_SERVICE" || error_exit "Failed to start backend service"

# Wait for service to be fully started
sleep 3

# Check if service is running
if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    log_success "Backend service started successfully"
else
    error_exit "Backend service failed to start. Check: journalctl -u $BACKEND_SERVICE -n 50"
fi

log "Reloading nginx..."
systemctl reload "$NGINX_SERVICE" || error_exit "Failed to reload nginx"
log_success "Nginx reloaded"

#===============================================================================
# Verify Services
#===============================================================================

log "Verifying services..."

# Check backend service status
if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    log_success "Backend service is running"
else
    log_error "Backend service is not running"
    log_error "Check logs: journalctl -u $BACKEND_SERVICE -n 50"
    exit 1
fi

# Check nginx service status
if systemctl is-active --quiet "$NGINX_SERVICE"; then
    log_success "Nginx service is running"
else
    log_error "Nginx service is not running"
    exit 1
fi

# Test backend health endpoint (if accessible)
if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
    log_success "Backend health check passed"
else
    log_warning "Backend health check failed (endpoint may not exist)"
fi

#===============================================================================
# Cleanup and Summary
#===============================================================================

log ""
log "=== Update Summary ==="
log "Application directory: $APP_DIR"
log "Git branch: $GIT_BRANCH"
if [[ "$SKIP_BACKUP" == false ]] && [[ -f "$BACKUP_FILE" ]]; then
    log "Database backup: $BACKUP_FILE"
    log "Config backups: $BACKUP_DIR/*-env-$TIMESTAMP"
fi
log "Backend service: $BACKEND_SERVICE ($(systemctl is-active $BACKEND_SERVICE))"
log "Nginx service: $NGINX_SERVICE ($(systemctl is-active $NGINX_SERVICE))"
log "Log file: $LOG_FILE"
log ""
log_success "Update completed successfully!"
log ""
log "Next steps:"
log "  1. Test the application in your browser"
log "  2. Verify login and core functionality work"
log "  3. Check backend logs: journalctl -u $BACKEND_SERVICE -f"
log "  4. Check nginx logs: tail -f /var/log/nginx/recipe-catalog-error.log"
if [[ "$SKIP_BACKUP" == false ]] && [[ -f "$BACKUP_FILE" ]]; then
    log ""
    log "If you encounter issues, rollback with:"
    log "  sudo systemctl stop $BACKEND_SERVICE"
    log "  sudo cp $BACKUP_FILE $APP_DIR/backend/recipes.db"
    log "  sudo cp $BACKUP_DIR/backend-env-$TIMESTAMP $APP_DIR/backend/.env"
    log "  sudo cp $BACKUP_DIR/frontend-env-$TIMESTAMP $APP_DIR/frontend/.env"
    log "  sudo systemctl start $BACKEND_SERVICE"
fi
log ""

exit 0
