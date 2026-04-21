#!/bin/bash
# =============================================================================
# Odometer Labs — Carputer Pi Setup Script
# =============================================================================
# Usage: bash setup.sh
# Run this script on a fresh Raspberry Pi OS Lite (64-bit) install.
# Idempotent — safe to run multiple times.
#
# Prerequisites:
#   - Raspberry Pi OS Lite (64-bit) flashed and booted
#   - SSH access established
#   - Internet connection available
#   - u-blox C099-F9P connected via data-capable micro-USB cable
#
# What this script does:
#   1. Installs required packages (vim, git, gpsd, chrony, postgresql)
#   2. Installs Docker and adds user to docker group
#   3. Configures gpsd for u-blox GPS module
#   4. Enables and starts required systemd services
#   5. Clones the carputer repo to /opt/carputer
#   6. Deploys chrony GPS time discipline config and gpsd drop-in
#   7. Deploys carputer.service
#   8. Sets up Docker environment (.env) and pulls containers
# =============================================================================

set -e  # Exit immediately on error

# -----------------------------------------------------------------------------
# Colors for output
# -----------------------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
REPO_URL="https://github.com/odometer-labs/carputer.git"
DEPLOY_DIR="/opt/carputer"
CURRENT_USER=$(whoami)

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
confirm() {
    read -r -p "$1 [y/N]: " response
    [[ "$response" =~ ^[Yy]$ ]]
}

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
echo ""
echo "============================================="
echo "   Odometer Labs — Carputer Pi Setup Script  "
echo "============================================="
echo ""
warn "This script will install packages and modify system configuration."
warn "Ensure the u-blox C099-F9P is connected via a data-capable micro-USB cable."
echo ""
confirm "Do you want to proceed?" || { echo "Aborted."; exit 0; }
echo ""

# -----------------------------------------------------------------------------
# Step 1 — System update and package installation
# -----------------------------------------------------------------------------
info "Step 1: Installing required packages..."
info "  Packages: vim, git, gpsd, gpsd-clients, chrony, curl"
info "  (PostgreSQL is provided by Docker, not installed on system)"
echo ""
confirm "Proceed with package installation?" || { warn "Skipping package installation."; }

sudo apt update
sudo apt install -y vim git gpsd gpsd-clients chrony curl

info "Packages installed successfully."
echo ""

# -----------------------------------------------------------------------------
# Step 2 — Install Docker
# -----------------------------------------------------------------------------
info "Step 2: Installing Docker and plugins..."

# Detect architecture for plugin downloads
ARCH=$(uname -m)
case "$ARCH" in
    aarch64) DOCKER_ARCH="linux-arm64" ;;
    x86_64)  DOCKER_ARCH="linux-amd64" ;;
    armv7l)  DOCKER_ARCH="linux-armv7" ;;
    *)       DOCKER_ARCH="linux-amd64" ;;
esac
info "Detected architecture: $ARCH -> $DOCKER_ARCH"

# Install Docker if not present
if command -v docker &>/dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    info "Docker is already installed (version $DOCKER_VERSION)."
else
    confirm "Install Docker using the official convenience script?" || { warn "Skipping Docker installation."; }

    info "Downloading and running Docker install script..."
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    rm /tmp/get-docker.sh
    info "Docker installed successfully."
fi

# Create CLI plugins directory
sudo mkdir -p /usr/local/lib/docker/cli-plugins

# Ensure Docker Compose v2 plugin is installed
if docker compose version &>/dev/null 2>&1; then
    COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || echo "installed")
    info "Docker Compose plugin is installed (version $COMPOSE_VERSION)."
else
    info "Installing Docker Compose plugin..."
    sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-${DOCKER_ARCH}" \
        -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    info "Docker Compose plugin installed."
fi

# Ensure Docker Buildx plugin is installed (required for BuildKit)
# NOTE: Docker Compose requires buildx >= 0.17.0
MIN_BUILDX_VERSION="0.17.0"
BUILDX_INSTALL_VERSION="0.17.1"

install_buildx() {
    info "Installing Docker Buildx plugin v${BUILDX_INSTALL_VERSION}..."
    sudo curl -SL "https://github.com/docker/buildx/releases/download/v${BUILDX_INSTALL_VERSION}/buildx-v${BUILDX_INSTALL_VERSION}.${DOCKER_ARCH}" \
        -o /usr/local/lib/docker/cli-plugins/docker-buildx
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx
    info "Docker Buildx plugin installed."
}

if docker buildx version &>/dev/null 2>&1; then
    BUILDX_VERSION=$(docker buildx version 2>/dev/null | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1 | tr -d 'v')
    info "Docker Buildx plugin is installed (v$BUILDX_VERSION)."
    # Check if version meets minimum requirement
    if [ -n "$BUILDX_VERSION" ]; then
        BUILDX_MAJOR=$(echo "$BUILDX_VERSION" | cut -d. -f1)
        BUILDX_MINOR=$(echo "$BUILDX_VERSION" | cut -d. -f2)
        MIN_MAJOR=$(echo "$MIN_BUILDX_VERSION" | cut -d. -f1)
        MIN_MINOR=$(echo "$MIN_BUILDX_VERSION" | cut -d. -f2)
        if [ "$BUILDX_MAJOR" -lt "$MIN_MAJOR" ] || { [ "$BUILDX_MAJOR" -eq "$MIN_MAJOR" ] && [ "$BUILDX_MINOR" -lt "$MIN_MINOR" ]; }; then
            warn "Buildx v$BUILDX_VERSION is below minimum v$MIN_BUILDX_VERSION required by Docker Compose."
            install_buildx
        fi
    fi
else
    install_buildx
fi

# Enable BuildKit by default
if grep -q "DOCKER_BUILDKIT=1" /etc/environment 2>/dev/null; then
    info "BuildKit is already enabled."
else
    info "Enabling BuildKit by default..."
    echo 'DOCKER_BUILDKIT=1' | sudo tee -a /etc/environment > /dev/null
    export DOCKER_BUILDKIT=1
    info "BuildKit enabled."
fi

# Add current user to docker group (allows running docker without sudo)
if groups "$CURRENT_USER" | grep -q '\bdocker\b'; then
    info "User $CURRENT_USER is already in the docker group."
else
    confirm "Add $CURRENT_USER to the docker group (run docker without sudo)?" || { warn "Skipping docker group."; }
    sudo usermod -aG docker "$CURRENT_USER"
    info "User $CURRENT_USER added to docker group."
    warn "You must log out and back in (or run 'newgrp docker') for this to take effect."
fi

# Enable Docker to start on boot
if systemctl is-enabled docker &>/dev/null; then
    info "Docker is already enabled to start on boot."
else
    sudo systemctl enable docker
    sudo systemctl start docker
    info "Docker enabled and started."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 3 — Configure gpsd
# -----------------------------------------------------------------------------
info "Step 3: Configuring gpsd..."

GPSD_CONFIG="/etc/default/gpsd"

# Check if already configured
if grep -q 'DEVICES="/dev/ttyACM0"' "$GPSD_CONFIG" && \
   grep -q 'GPSD_OPTIONS="-F /var/run/gpsd.sock"' "$GPSD_CONFIG"; then
    info "gpsd is already configured correctly — skipping."
else
    confirm "Update $GPSD_CONFIG with correct DEVICES and GPSD_OPTIONS?" || { warn "Skipping gpsd config."; }

    sudo sed -i 's|^DEVICES=.*|DEVICES="/dev/ttyACM0"|' "$GPSD_CONFIG"
    sudo sed -i 's|^GPSD_OPTIONS=.*|GPSD_OPTIONS="-F /var/run/gpsd.sock"|' "$GPSD_CONFIG"

    info "gpsd configuration updated:"
    info "  DEVICES=/dev/ttyACM0"
    info "  GPSD_OPTIONS=-F /var/run/gpsd.sock"
fi
echo ""

# -----------------------------------------------------------------------------
# Step 4 — Enable and start systemd services
# -----------------------------------------------------------------------------
info "Step 4: Enabling and starting required systemd services..."
info "  Services: chrony, gpsd, postgresql, docker"
echo ""
confirm "Proceed with enabling services?" || { warn "Skipping service setup."; }

# chrony — high precision time sync (required by gpsd for RTK)
if systemctl is-enabled chrony &>/dev/null && systemctl is-active chrony &>/dev/null; then
    info "chrony is already enabled and running — skipping."
else
    sudo systemctl enable chrony
    sudo systemctl start chrony
    info "chrony enabled and started."
fi

# gpsd — GPS daemon
if systemctl is-enabled gpsd &>/dev/null && systemctl is-active gpsd &>/dev/null; then
    info "gpsd is already enabled and running — skipping."
else
    sudo systemctl enable gpsd
    sudo systemctl start gpsd
    info "gpsd enabled and started."
fi

# postgresql — system postgres NOT needed (using Docker postgres instead)
# Stop and disable system postgres to avoid port 5432 conflict with Docker
# Check for both generic 'postgresql' and versioned services like 'postgresql@14-main'
POSTGRES_SERVICES=$(systemctl list-units --type=service --all 2>/dev/null | grep -E 'postgresql' | awk '{print $1}' | tr '\n' ' ')

if [ -n "$POSTGRES_SERVICES" ]; then
    for svc in $POSTGRES_SERVICES; do
        if systemctl is-active "$svc" &>/dev/null 2>&1; then
            warn "System PostgreSQL service '$svc' is running and will conflict with Docker on port 5432."
            if confirm "Stop and disable $svc? (Docker will provide PostgreSQL instead)"; then
                sudo systemctl stop "$svc"
                sudo systemctl disable "$svc"
                info "$svc stopped and disabled."
            else
                warn "$svc left running. Docker PostgreSQL will fail to bind port 5432."
            fi
        elif systemctl is-enabled "$svc" &>/dev/null 2>&1; then
            info "System PostgreSQL service '$svc' is enabled but not running."
            if confirm "Disable $svc to prevent future conflicts?"; then
                sudo systemctl disable "$svc"
                info "$svc disabled."
            fi
        fi
    done
else
    info "No system PostgreSQL services found — good, Docker will provide PostgreSQL."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 5 — Clone repo to /opt/carputer
# -----------------------------------------------------------------------------
info "Step 5: Setting up carputer repository at /opt/carputer..."

if [ -d "$DEPLOY_DIR/.git" ]; then
    info "Repository already exists at $DEPLOY_DIR."
    confirm "Pull latest changes?" && sudo git -C "$DEPLOY_DIR" pull && info "Repository updated."
else
    confirm "Clone $REPO_URL into $DEPLOY_DIR?" || { warn "Skipping repo clone."; }

    sudo mkdir -p "$DEPLOY_DIR"
    sudo git clone "$REPO_URL" "$DEPLOY_DIR"
    sudo chown -R "$CURRENT_USER":"$CURRENT_USER" "$DEPLOY_DIR"
    info "Repository cloned to $DEPLOY_DIR."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 6 — Deploy chrony config and gpsd drop-in for GPS time discipline
# -----------------------------------------------------------------------------
info "Step 6: Deploying chrony + GPSD time sync configuration..."

CHRONY_SRC="$DEPLOY_DIR/embedded/ntp_gps_sync/chrony.conf"
CHRONY_DST="/etc/chrony/chrony.conf"
GPSD_DROPIN_SRC="$DEPLOY_DIR/embedded/ntp_gps_sync/gpsd-depends-chrony.conf"
GPSD_DROPIN_DIR="/etc/systemd/system/gpsd.service.d"
GPSD_DROPIN_DST="$GPSD_DROPIN_DIR/depends-chrony.conf"

# Deploy chrony.conf (GPS SHM refclocks + NTP fallback)
if [ -f "$CHRONY_SRC" ]; then
    if diff -q "$CHRONY_SRC" "$CHRONY_DST" &>/dev/null; then
        info "chrony.conf is already up to date — skipping."
    else
        confirm "Deploy GPS-disciplined chrony.conf to /etc/chrony/?" || { warn "Skipping chrony config."; }
        sudo cp "$CHRONY_DST" "$CHRONY_DST.bak" 2>/dev/null || true
        sudo cp "$CHRONY_SRC" "$CHRONY_DST"
        info "chrony.conf deployed (backup at $CHRONY_DST.bak)."
    fi
else
    warn "chrony.conf not found at $CHRONY_SRC — skipping."
fi

# Deploy gpsd drop-in (ensures gpsd starts after chrony)
if [ -f "$GPSD_DROPIN_SRC" ]; then
    sudo mkdir -p "$GPSD_DROPIN_DIR"
    if diff -q "$GPSD_DROPIN_SRC" "$GPSD_DROPIN_DST" &>/dev/null; then
        info "gpsd chrony drop-in already up to date — skipping."
    else
        confirm "Deploy gpsd drop-in to ensure chrony starts before gpsd?" || { warn "Skipping gpsd drop-in."; }
        sudo cp "$GPSD_DROPIN_SRC" "$GPSD_DROPIN_DST"
        sudo systemctl daemon-reload
        info "gpsd drop-in deployed: gpsd.service now requires chrony.service."
    fi
else
    warn "gpsd drop-in not found at $GPSD_DROPIN_SRC — skipping."
fi
echo ""

# Restart chrony to pick up new config if deployed
if systemctl is-active chrony &>/dev/null; then
    sudo systemctl restart chrony
    info "chrony restarted with updated configuration."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 7 — Deploy carputer.service
# -----------------------------------------------------------------------------
info "Step 7: Deploying carputer.service..."

SERVICE_SRC="$DEPLOY_DIR/infrastructure/systemd/carputer.service"
SERVICE_DST="/etc/systemd/system/carputer.service"

if [ ! -f "$SERVICE_SRC" ]; then
    error "carputer.service not found at $SERVICE_SRC. Ensure the repo was cloned correctly."
fi

if diff -q "$SERVICE_SRC" "$SERVICE_DST" &>/dev/null; then
    info "carputer.service is already up to date — skipping."
else
    confirm "Deploy carputer.service to /etc/systemd/system/?" || { warn "Skipping service deployment."; }

    sudo cp "$SERVICE_SRC" "$SERVICE_DST"
    sudo systemctl daemon-reload
    sudo systemctl enable carputer
    info "carputer.service deployed and enabled."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 8 — Set up Docker environment
# -----------------------------------------------------------------------------
info "Step 8: Setting up Docker environment..."

ENV_EXAMPLE="$DEPLOY_DIR/.env.example"
ENV_FILE="$DEPLOY_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    info ".env file already exists at $ENV_FILE — skipping."
else
    if [ -f "$ENV_EXAMPLE" ]; then
        confirm "Create .env from .env.example? (You can edit credentials later)" || { warn "Skipping .env setup."; }
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        info ".env file created at $ENV_FILE"
        warn "Edit $ENV_FILE to set your database credentials before starting containers."
    else
        warn ".env.example not found at $ENV_EXAMPLE — skipping .env setup."
    fi
fi

# Optionally pull/build Docker containers
if command -v docker &>/dev/null && [ -f "$ENV_FILE" ]; then
    echo ""
    if confirm "Pull and build Docker containers now? (This may take a few minutes on first run)"; then
        cd "$DEPLOY_DIR"
        info "Building Docker containers..."
        docker compose build
        info "Docker containers built successfully."
        echo ""
        if confirm "Start Docker containers now?"; then
            # Check if port 5432 is already in use before attempting to start
            if ss -tlnp 2>/dev/null | grep -q ':5432 ' || lsof -i :5432 &>/dev/null 2>&1; then
                PORT_PROCESS=$(ss -tlnp 2>/dev/null | grep ':5432 ' | head -1 || lsof -i :5432 2>/dev/null | tail -1)
                error "Port 5432 is already in use! Docker PostgreSQL cannot start.

Process using port 5432:
  $PORT_PROCESS

To fix this:
  1. Stop the conflicting service:
     sudo systemctl stop postgresql
     sudo systemctl disable postgresql
  2. Or check for all postgres services:
     systemctl list-units --type=service | grep postgres
  3. Then re-run: docker compose up -d

Aborting to prevent container startup failure."
            fi
            docker compose up -d
            info "Docker containers started."
            info "  Frontend at: http://localhost:3000"
            info "  API available at: http://localhost:8000"
            info "  API docs at: http://localhost:8000/docs"
            info "  Adminer (DB admin) at: http://localhost:8080"
        else
            warn "Containers built but not started. Run 'docker compose up -d' when ready."
        fi
    else
        warn "Skipping Docker build. Run 'cd $DEPLOY_DIR && docker compose up -d' when ready."
    fi
fi
echo ""

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo "============================================="
info "Setup complete!"
echo ""
echo "  GPS device  : /dev/ttyACM0"
echo "  gpsd socket : /var/run/gpsd.sock"
echo "  Repo        : $DEPLOY_DIR"
echo ""
echo "  Services enabled:"
echo "    ✓ chrony (GPS time sync)"
echo "    ✓ gpsd (GPS daemon)"
echo "    ✓ docker (container runtime)"
echo "    ✓ carputer (auto-start on boot)"
echo "    - PostgreSQL runs in Docker (not as system service)"
echo ""
echo "  Docker services (when running):"
echo "    • Frontend: http://localhost:3000"
echo "    • API:      http://localhost:8000"
echo "    • Swagger:  http://localhost:8000/docs"
echo "    • Adminer:  http://localhost:8080"
echo ""
warn "NEXT STEPS:"
warn "  1. Edit $DEPLOY_DIR/.env with your database credentials"
warn "  2. Start containers: cd $DEPLOY_DIR && docker compose up -d"
warn "  3. Open frontend: http://localhost:3000"
echo ""
warn "NOTE: If you just added yourself to the docker group, log out"
warn "and back in (or run 'newgrp docker') before running docker commands."
echo ""
warn "NOTE: To enable SSH key access to GitHub for write access,"
warn "generate a key with: ssh-keygen -t ed25519 -C 'carputer-pi4'"
warn "and add the public key as a deploy key in the GitHub repo settings."
echo "============================================="
