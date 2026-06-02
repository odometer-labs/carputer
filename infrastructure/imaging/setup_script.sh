#!/bin/bash
# =============================================================================
# Odometer Labs — Carputer Pi Setup Script (INTEGRATED WITH DIREWOLF/APRS)
# =============================================================================
# Usage: bash setup.sh
# Run this script on a fresh Raspberry Pi OS Lite (64-bit) install.
# Idempotent — safe to run multiple times.
#
# Prerequisites:
#   - Raspberry Pi OS Lite (64-bit) flashed and booted
#   - SSH access established
#   - Internet connection available
#   - u-blox C099-F9P connected via USB-C cable
#   - RTL-SDR USB dongle connected (for APRS)
#
# What this script does:
#   1. Installs required packages (vim, git, gpsd, chrony, postgresql)
#   2. Installs Docker and adds user to docker group
#   3. Configures gpsd for u-blox GPS module
#   4. Installs RTL-SDR drivers and blacklists conflicting modules
#   5. Builds and installs Direwolf (APRS decoder)
#   6. Clones the carputer repo to /opt/carputer
#   7. Deploys chrony GPS time discipline config and gpsd drop-in
#   8. Deploys carputer.service
#   9. Deploys APRS infrastructure (services + database)
#  10. Sets up Docker environment (.env) and pulls containers
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
CURRENT_USER=carputer
IMAGING_DIR=$DEPLOY_DIR/infrastructure/imaging

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
echo ""
echo "=================================================================="
echo "   Odometer Labs — Carputer Pi Setup Script (with APRS Support)  "
echo "=================================================================="
echo ""
warn "This script will install packages and modify system configuration."
warn "Ensure the u-blox C099-F9P is connected via USB-C cable."
warn "Ensure the RTL-SDR USB dongle is connected (for APRS reception)."
echo ""


cd $IMAGING_DIR

# -----------------------------------------------------------------------------
# Step 1 — System update and package installation
# -----------------------------------------------------------------------------
info "Step 1: Installing required packages..."
info "  Base: vim, git, curl"
info "  GPS: gpsd, gpsd-clients, chrony"
info "  RTL-SDR: rtl-sdr"
info "  Direwolf deps: cmake, gcc, g++, make, libasound2-dev"
info "  Python: python3-requests"

DEBIAN_FRONTEND=noninteractive apt update && xargs -a packages.txt apt-get install -y

info "Packages installed successfully."
echo ""

# -----------------------------------------------------------------------------
# Step 2 — Install Docker
# -----------------------------------------------------------------------------
info "Step 2: Installing Docker and plugins..."

# Detect architecture for plugin downloads
ARCH=$(uname -m)
case "$ARCH" in
    aarch64)
        COMPOSE_ARCH="linux-aarch64"
        BUILDX_ARCH="linux-arm64"
        ;;
    x86_64)
        COMPOSE_ARCH="linux-x86_64"
        BUILDX_ARCH="linux-amd64"
        ;;
    armv7l)
        COMPOSE_ARCH="linux-armv7"
        BUILDX_ARCH="linux-armv7"
        ;;
    *)
        COMPOSE_ARCH="linux-x86_64"
        BUILDX_ARCH="linux-amd64"
        ;;
esac
info "Detected architecture: $ARCH (Compose: $COMPOSE_ARCH, Buildx: $BUILDX_ARCH)"

# Install Docker if not present
if command -v docker &>/dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    info "Docker is already installed (version $DOCKER_VERSION)."
else
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
    sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-${COMPOSE_ARCH}" \
        -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    info "Docker Compose plugin installed."
fi

# Ensure Docker Buildx plugin is installed (required for BuildKit)
MIN_BUILDX_VERSION="0.17.0"
BUILDX_INSTALL_VERSION="0.17.1"

install_buildx() {
    info "Installing Docker Buildx plugin v${BUILDX_INSTALL_VERSION}..."
    sudo curl -SL "https://github.com/docker/buildx/releases/download/v${BUILDX_INSTALL_VERSION}/buildx-v${BUILDX_INSTALL_VERSION}.${BUILDX_ARCH}" \
        -o /usr/local/lib/docker/cli-plugins/docker-buildx
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx
    info "Docker Buildx plugin installed."
}

if docker buildx version &>/dev/null 2>&1; then
    BUILDX_VERSION=$(docker buildx version 2>/dev/null | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1 | tr -d 'v')
    info "Docker Buildx plugin is installed (v$BUILDX_VERSION)."
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

# Add current user to docker group
if groups "$CURRENT_USER" | grep -q '\bdocker\b'; then
    info "User $CURRENT_USER is already in the docker group."
else
    sudo usermod -aG docker "$CURRENT_USER"
    info "User $CURRENT_USER added to docker group."
    warn "You must log out and back in (or run 'newgrp docker') for this to take effect."
fi

# Enable Docker to start on boot
if systemctl is-enabled docker &>/dev/null; then
    info "Docker is already enabled to start on boot."
else
    sudo systemctl enable docker
    info "Docker enabled"
fi
echo ""

# -----------------------------------------------------------------------------
# Step 3 — Configure gpsd
# -----------------------------------------------------------------------------
info "Step 3: Configuring gpsd..."

GPSD_CONFIG="/etc/default/gpsd"

# Check if already configured
if grep -q 'DEVICES="/dev/ttyACM0"' "$GPSD_CONFIG" && \
   grep -q 'GPSD_OPTIONS="-n"' "$GPSD_CONFIG" && \
   grep -q 'START_DAEMON="true"' "$GPSD_CONFIG"; then
    info "gpsd is already configured."
else
    # Backup existing config
    sudo cp "$GPSD_CONFIG" "$GPSD_CONFIG.bak" 2>/dev/null || true

    # Write new config
    sudo cp files/gpsd "$GPSD_CONFIG"
    info "gpsd configured for /dev/ttyACM0 (backup at $GPSD_CONFIG.bak)."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 4 — Configure RTL-SDR and blacklist conflicting drivers
# -----------------------------------------------------------------------------
info "Step 4: Configuring RTL-SDR..."

BLACKLIST_FILE="/etc/modprobe.d/blacklist-rtl.conf"

if [ -f "$BLACKLIST_FILE" ]; then
    info "RTL-SDR blacklist already exists at $BLACKLIST_FILE."
else
    sudo cp files/blacklist-rtl.conf "$BLACKLIST_FILE"
    info "RTL-SDR blacklist created at $BLACKLIST_FILE."
fi

# Add user to plugdev group for RTL-SDR access
if groups "$CURRENT_USER" | grep -q '\bplugdev\b'; then
    info "User $CURRENT_USER is already in the plugdev group."
else
    sudo usermod -aG plugdev "$CURRENT_USER"
    info "User $CURRENT_USER added to plugdev group."
    warn "You must log out and back in for this to take effect."
fi

# Test RTL-SDR detection
if lsusb | grep -qi rtl; then
    info "RTL-SDR device detected via USB."
else
    warn "RTL-SDR device not detected. Ensure dongle is connected."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 5 — Build and install Direwolf
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Step 5 — Build and install Direwolf
# -----------------------------------------------------------------------------
info "Step 5: Building and installing Direwolf..."

# Check if Direwolf is already installed
if command -v direwolf &>/dev/null; then
    DIREWOLF_VERSION=$(direwolf -v 2>&1 | head -1 || echo "installed")
    info "Direwolf is already installed ($DIREWOLF_VERSION)."
fi

# Clone and build Direwolf
DIREWOLF_DIR="/opt/direwolf"

if [ ! -d "$DIREWOLF_DIR" ]; then
    info "Cloning Direwolf repository..."
    git clone https://github.com/wb2osz/direwolf "$DIREWOLF_DIR"
else
    info "Direwolf repository already exists at $DIREWOLF_DIR."
fi

info "Building Direwolf (this may take 5-10 minutes)..."
cd "$DIREWOLF_DIR"
mkdir -p build
cd build
cmake ..
make -j4
sudo make install
sudo make install-conf

info "Direwolf installed successfully."
echo ""

cd $IMAGING_DIR


# -----------------------------------------------------------------------------
# Step 6 — Enable and start systemd services
# -----------------------------------------------------------------------------
info "Step 6: Configuring APRS reception..."

APRS_DIR="/opt/aprs"

# Create APRS directory
sudo mkdir -p "$APRS_DIR"
sudo mkdir -p /var/log/carputer/aprs
sudo chown -R "$CURRENT_USER":"$CURRENT_USER" "$APRS_DIR"
sudo chown -R "$CURRENT_USER":"$CURRENT_USER" /var/log/carputer

# Deploy Direwolf configuration
DIREWOLF_CONF="$APRS_DIR/direwolf.conf"
APRS_SCRIPT="$APRS_DIR/start_aprs.sh"

if [ -f "$DIREWOLF_CONF" ]; then
    info "Direwolf config already exists at $DIREWOLF_CONF."
else
    info "Copying Direwolf configuration..."
    cp files/direwolf.conf "$DIREWOLF_CONF"
    info "Direwolf configuration created at $DIREWOLF_CONF."

    info "Copying APRS script..."
    cp  files/start_aprs.sh "$APRS_SCRIPT"
    chmod +x "$APRS_SCRIPT"
    info "APRS reception script created at $APRS_SCRIPT."
    echo ""
fi

# -----------------------------------------------------------------------------
# Step 7 — Deploy APRS bridge to backend
# -----------------------------------------------------------------------------
info "Step 7: Deploying APRS bridge from embedded/aprs_bridge..."

APRS_BRIDGE_DIR="/opt/aprs_bridge"

# Copy the APRS bridge module from the repo
if [ -d "$DEPLOY_DIR/embedded/aprs_bridge" ]; then
    if [ -d "$APRS_BRIDGE_DIR" ]; then
        info "APRS bridge already exists at $APRS_BRIDGE_DIR."
    fi
    cp -r "$DEPLOY_DIR/embedded/aprs_bridge" "$APRS_DIR/"
    info "APRS bridge deployed from embedded/aprs_bridge."
else
    warn "embedded/aprs_bridge not found in repo — creating minimal bridge..."
    mkdir -p "$APRS_BRIDGE_DIR"
    # TODO copy bridge
fi
info "APRS bridge ready at $APRS_BRIDGE_DIR."
echo ""

# -----------------------------------------------------------------------------
# Step 8 — Deploy systemd services for APRS
# -----------------------------------------------------------------------------
info "Step 8: Deploying APRS systemd services..."

# APRS receiver service
APRS_RECEIVER_SERVICE="/etc/systemd/system/aprs-receiver.service"

sudo cp files/aprs-receiver.service "$APRS_RECEIVER_SERVICE"
info "APRS receiver service created at $APRS_RECEIVER_SERVICE."

# APRS bridge service
APRS_BRIDGE_SERVICE="/etc/systemd/system/aprs-bridge.service"

sudo cp files/aprs-bridge.service "$APRS_BRIDGE_SERVICE"
info "APRS bridge service created at $APRS_BRIDGE_SERVICE."

# Reload systemd and enable services
sudo systemctl daemon-reload

sudo systemctl enable aprs-receiver
sudo systemctl enable aprs-bridge
info "APRS services enabled."

# -----------------------------------------------------------------------------
# Step 9 — Enable and start systemd services
# -----------------------------------------------------------------------------
info "Step 9: Enabling and starting systemd services..."

# chrony — GPS time sync
if systemctl is-enabled chrony &>/dev/null; then
    info "chrony is already enabled."
else
    sudo systemctl enable chrony
    sudo systemctl start chrony
    info "chrony enabled and started."
fi

# gpsd — GPS daemon
if systemctl is-enabled gpsd &>/dev/null; then
    info "gpsd is already enabled."
else
    sudo systemctl enable gpsd
    sudo systemctl start gpsd
    info "gpsd enabled and started."
fi

# -----------------------------------------------------------------------------
# Step 7 — Clone repo to /opt/carputer
# -----------------------------------------------------------------------------
info "Step 7: Setting up carputer repository at /opt/carputer..."

if [ -d "$DEPLOY_DIR/.git" ]; then
    info "Repository already exists at $DEPLOY_DIR."
    sudo git -C "$DEPLOY_DIR" pull && info "Repository updated."
else
    sudo mkdir -p "$DEPLOY_DIR"
    sudo git clone "$REPO_URL" "$DEPLOY_DIR"
    sudo chown -R "$CURRENT_USER":"$CURRENT_USER" "$DEPLOY_DIR"
    info "Repository cloned to $DEPLOY_DIR."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 8 — Deploy chrony config and gpsd drop-in
# -----------------------------------------------------------------------------
info "Step 8: Deploying chrony + GPSD time sync configuration..."

CHRONY_SRC="$DEPLOY_DIR/embedded/ntp_gps_sync/chrony.conf"
CHRONY_DST="/etc/chrony/chrony.conf"
GPSD_DROPIN_SRC="$DEPLOY_DIR/embedded/ntp_gps_sync/gpsd-depends-chrony.conf"
GPSD_DROPIN_DIR="/etc/systemd/system/gpsd.service.d"
GPSD_DROPIN_DST="$GPSD_DROPIN_DIR/depends-chrony.conf"

# Deploy chrony.conf
if [ -f "$CHRONY_SRC" ]; then
    if diff -q "$CHRONY_SRC" "$CHRONY_DST" &>/dev/null; then
        info "chrony.conf is already up to date."
    else
        sudo cp "$CHRONY_DST" "$CHRONY_DST.bak" 2>/dev/null || true
        sudo cp "$CHRONY_SRC" "$CHRONY_DST"
        info "chrony.conf deployed (backup at $CHRONY_DST.bak)."
    fi
else
    warn "chrony.conf not found at $CHRONY_SRC — skipping."
fi

# Deploy gpsd drop-in
if [ -f "$GPSD_DROPIN_SRC" ]; then
    sudo mkdir -p "$GPSD_DROPIN_DIR"
    if diff -q "$GPSD_DROPIN_SRC" "$GPSD_DROPIN_DST" &>/dev/null; then
        info "gpsd drop-in already up to date."
    else
        sudo cp "$GPSD_DROPIN_SRC" "$GPSD_DROPIN_DST"
        sudo systemctl daemon-reload
        info "gpsd drop-in deployed."
    fi
else
    warn "gpsd drop-in not found at $GPSD_DROPIN_SRC — skipping."
fi

# Restart chrony
if systemctl is-active chrony &>/dev/null; then
    sudo systemctl restart chrony
    info "chrony restarted."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 9 — Deploy carputer.service
# -----------------------------------------------------------------------------
info "Step 9: Deploying carputer.service..."

SERVICE_SRC="$DEPLOY_DIR/infrastructure/imaging/services/carputer.service"
SERVICE_DST="/etc/systemd/system/carputer.service"

if [ ! -f "$SERVICE_SRC" ]; then
    warn "carputer.service not found at $SERVICE_SRC — skipping."
else
    if diff -q "$SERVICE_SRC" "$SERVICE_DST" &>/dev/null; then
        info "carputer.service is already up to date."
    else
        sudo cp "$SERVICE_SRC" "$SERVICE_DST"
        sudo systemctl daemon-reload
        sudo systemctl enable carputer
        info "carputer.service deployed and enabled."
    fi
fi
echo ""

# -----------------------------------------------------------------------------
# Step 10 — Deploy APRS infrastructure
# -----------------------------------------------------------------------------
info "Step 10: Deploying APRS infrastructure..."

APRS_DEPLOY_SCRIPT="$DEPLOY_DIR/infrastructure/imaging/files/deploy_aprs.sh"

if [ ! -f "$APRS_DEPLOY_SCRIPT" ]; then
    warn "APRS deployment script not found at $APRS_DEPLOY_SCRIPT"
    warn "APRS infrastructure will need to be deployed manually."
    warn "Skipping APRS deployment."
else
    # Make sure script is executable
    chmod +x "$APRS_DEPLOY_SCRIPT"
    
    # Run the APRS deployment script
    cd "$DEPLOY_DIR"
    bash "$APRS_DEPLOY_SCRIPT"
    
    info "APRS infrastructure deployed."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 11 — Set up Docker environment
# -----------------------------------------------------------------------------
info "Step 11: Setting up Docker environment..."

ENV_EXAMPLE="$DEPLOY_DIR/.env.example"
ENV_FILE="$DEPLOY_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    info ".env file already exists."
else
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        info ".env file created at $ENV_FILE"
        warn "Edit $ENV_FILE to set your database credentials."
    else
        warn ".env.example not found — skipping .env setup."
    fi
fi

# -----------------------------------------------------------------------------
# Step 12 — Start APRS services (if deployed)
# -----------------------------------------------------------------------------
if systemctl list-unit-files | grep -q aprs-receiver.service; then
    info "Step 12: Starting APRS services..."
    sudo systemctl start aprs-receiver
    sleep 3
    sudo systemctl start aprs-bridge
    info "APRS services started."
    info "  Check status: sudo systemctl status aprs-receiver aprs-bridge"
    info "  View logs:    sudo journalctl -u aprs-receiver -f"
    echo ""
fi

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo "=================================================================="
info "Setup complete!"
echo ""
echo "  GPS device    : /dev/ttyACM0"
echo "  gpsd socket   : /var/run/gpsd.sock"
echo "  RTL-SDR       : 144.390 MHz (APRS)"
echo "  Direwolf KISS : localhost:8003"
echo "  Direwolf AGW  : localhost:8005"
echo "  Repo          : $DEPLOY_DIR"
echo ""
echo "  Services enabled:"
echo "    ✓ chrony (GPS time sync)"
echo "    ✓ gpsd (GPS daemon)"
echo "    ✓ docker (container runtime)"
echo "    ✓ carputer (auto-start on boot)"
if systemctl list-unit-files | grep -q aprs-receiver.service; then
    echo "    ✓ aprs-receiver (RTL-SDR + Direwolf)"
    echo "    ✓ aprs-bridge (KISS → Backend)"
fi
echo ""
echo "  Docker services:"
echo "    • Frontend: http://localhost:3000"
echo "    • API:      http://localhost:8000"
echo "    • Swagger:  http://localhost:8000/docs"
echo "    • Adminer:  http://localhost:8080"
echo ""
warn "NEXT STEPS:"
warn "  1. Edit $DEPLOY_DIR/.env with credentials"
warn "  2. Test GPS: cgps -s"
if systemctl list-unit-files | grep -q aprs-receiver.service; then
    warn "  3. Test APRS: sudo journalctl -u aprs-receiver -f"
    warn "  4. Check logs: tail -f /var/log/carputer/aprs/aprs-*.log"
    warn "  5. Test API: curl http://localhost:8000/v1/aprs/stations"
    warn "  6. Open frontend: http://localhost:3000"
else
    warn "  3. Deploy APRS: bash $DEPLOY_DIR/infrastructure/imaging/deploy_aprs.sh"
    warn "  4. Start APRS: sudo systemctl start aprs-receiver aprs-bridge"
    warn "  5. Open frontend: http://localhost:3000"
fi
echo ""
warn "REBOOT RECOMMENDED to load RTL-SDR driver and group changes."
echo "=================================================================="
