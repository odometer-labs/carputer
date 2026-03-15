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
#   1. Installs required packages
#   2. Configures gpsd
#   3. Enables and starts required systemd services
#   4. Deploys carputer.service from the repo
#   5. Clones the carputer repo to /opt/carputer
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
info "  Packages: vim, git, gpsd, gpsd-clients, chrony, postgresql"
echo ""
confirm "Proceed with package installation?" || { warn "Skipping package installation."; }

sudo apt update
sudo apt install -y vim git gpsd gpsd-clients chrony postgresql

info "Packages installed successfully."
echo ""

# -----------------------------------------------------------------------------
# Step 2 — Configure gpsd
# -----------------------------------------------------------------------------
info "Step 2: Configuring gpsd..."

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
# Step 3 — Enable and start systemd services
# -----------------------------------------------------------------------------
info "Step 3: Enabling and starting required systemd services..."
info "  Services: chrony, gpsd, postgresql"
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

# postgresql — database backend
if systemctl is-enabled postgresql &>/dev/null; then
    info "postgresql is already enabled — skipping."
else
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
    info "postgresql enabled and started."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 4 — Clone repo to /opt/carputer
# -----------------------------------------------------------------------------
info "Step 4: Setting up carputer repository at /opt/carputer..."

REPO_URL="https://github.com/odometer-labs/carputer.git"
DEPLOY_DIR="/opt/carputer"
CURRENT_USER=$(whoami)

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
# Step 5 — Deploy carputer.service
# -----------------------------------------------------------------------------
info "Step 5: Deploying carputer.service..."

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
# Done
# -----------------------------------------------------------------------------
echo "============================================="
info "Setup complete!"
echo ""
echo "  GPS device  : /dev/ttyACM0"
echo "  gpsd socket : /var/run/gpsd.sock"
echo "  Repo        : $DEPLOY_DIR"
eho ""
echo "  Services enabled:"
echo "    ✓ chrony"
echo "    ✓ gpsd"
echo "    ✓ postgresql"
echo "    ✓ carputer"
echo ""
warn "NOTE: carputer.service will not start until the Python venv"
warn "and backend dependencies are installed. Connect with the"
warn "backend team for the next steps."
echo ""
warn "NOTE: To enable SSH key access to GitHub for write access,"
warn "generate a key with: ssh-keygen -t ed25519 -C 'carputer-pi4'"
warn "and add the public key as a deploy key in the GitHub repo settings."
echo "============================================="
