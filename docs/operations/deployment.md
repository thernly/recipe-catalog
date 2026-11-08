# Deployment

Two supported ways to run Recipe Catalog. Both use SQLite, and the backend applies Alembic migrations on deploy.

## Proxmox LXC (production)

The production deployment: a Debian LXC container with the backend under systemd (`recipe-catalog-backend`) and nginx serving the built frontend. `scripts/proxmox/deploy-lxc.sh` installs it and `scripts/proxmox/update-app.sh` updates it.

See [scripts/proxmox/README.md](../../scripts/proxmox/README.md).

## Docker Compose

Two containers (FastAPI backend and an nginx frontend that proxies `/api`), with the database in a named volume. The stack listens on `:8080`.

See the [Docker deployment guide](../docker/DOCKER-DEPLOYMENT.md).

The Cloudflare adapter and D1 mentioned elsewhere are not set up in this repo: there is no `wrangler.toml`, and the backend does not run on Workers.

For day-to-day operations (backups, logs, purging trash), see the [runbook](runbook.md).
