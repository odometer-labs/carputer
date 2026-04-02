#!/bin/bash
# =============================================================================
# Odometer Labs — RTL-SDR Driver Setup Script
# =============================================================================
# Usage: bash rtl-sdr-setup.sh
# Run this script on a Raspberry Pi running Raspberry Pi OS Lite (64-bit).
# Idempotent — safe to run multiple times.
#
# Prerequisites:
#   - Raspberry Pi OS Lite (64-bit) with internet access
#   - carputer base setup already completed (setup.sh)
#
# What this script does:
#   1. Purges any conflicting existing RTL-SDR drivers
#   2. Installs build dependencies
#   3. Clones and builds Osmocom RTL-SDR drivers from source
#   4. Installs udev rules
#   5. Blacklists the DVB-T kernel module permanently
#   6. Prompts for reboot
#
# RTL-SDR is used in the carputer project for passive APRS reception.
# No radio license is required for receive-only operation.
#
# Reference: https://www.rtl-sdr.com/rtl-sdr-quick-start-guide/
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Colors for output
# -----------------------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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
echo "   Odometer Labs — RTL-SDR Driver Setup      "
echo "============================================="
echo ""
warn "This script will install RTL-SDR drivers and modify kernel module config."
echo ""
confirm "Do you want to proceed?" || { echo "Aborted."; exit 0; }
echo ""

# -----------------------------------------------------------------------------
# Step 1 — Purge conflicting drivers if present
# -----------------------------------------------------------------------------
info "Step 1: Checking for conflicting RTL-SDR drivers..."

CONFLICTS_FOUND=false

dpkg -l | grep -i rtlsdr &>/dev/null && CONFLICTS_FOUND=true
ls /usr/lib/librtlsdr* /usr/local/lib/librtlsdr* /usr/local/bin/rtl_* &>/dev/null && CONFLICTS_FOUND=true

if [ "$CONFLICTS_FOUND" = true ]; then
    warn "Existing RTL-SDR drivers found — purging..."
    confirm "Purge existing drivers?" || { warn "Skipping purge — this may cause conflicts."; }

    sudo apt purge -y ^librtlsdr || true
    sudo rm -rvf /usr/lib/librtlsdr*
    sudo rm -rvf /usr/include/rtl-sdr*
    sudo rm -rvf /usr/local/lib/librtlsdr*
    sudo rm -rvf /usr/local/include/rtl-sdr*
    sudo rm -rvf /usr/local/include/rtl_*
    sudo rm -rvf /usr/local/bin/rtl_*

    info "Existing drivers purged."
else
    info "No conflicting drivers found — skipping purge."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 2 — Install build dependencies
# -----------------------------------------------------------------------------
info "Step 2: Installing build dependencies..."
info "  Packages: libusb-1.0-0-dev, git, cmake, pkg-config, build-essential"
echo ""
confirm "Proceed with package installation?" || { warn "Skipping dependency installation."; }

sudo apt-get update
sudo apt-get install -y libusb-1.0-0-dev git cmake pkg-config build-essential

info "Build dependencies installed."
echo ""

# -----------------------------------------------------------------------------
# Step 3 — Clone Osmocom RTL-SDR drivers
# -----------------------------------------------------------------------------
info "Step 3: Cloning Osmocom RTL-SDR drivers..."

CLONE_DIR="$HOME/rtl-sdr"

if [ -d "$CLONE_DIR/.git" ]; then
    info "Repository already exists at $CLONE_DIR."
    confirm "Pull latest changes?" && git -C "$CLONE_DIR" pull && info "Repository updated."
else
    confirm "Clone https://github.com/osmocom/rtl-sdr into $CLONE_DIR?" || { error "Cannot proceed without source — aborting."; }
    git clone https://github.com/osmocom/rtl-sdr "$CLONE_DIR"
    info "Repository cloned to $CLONE_DIR."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 4 — Build and install drivers
# -----------------------------------------------------------------------------
info "Step 4: Building RTL-SDR drivers..."

BUILD_DIR="$CLONE_DIR/build"

if [ -d "$BUILD_DIR" ]; then
    warn "Build directory already exists at $BUILD_DIR."
    confirm "Clean and rebuild?" && rm -rf "$BUILD_DIR" || info "Using existing build directory."
fi

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

cmake ../ -DINSTALL_UDEV_RULES=ON
make

info "Build complete."
echo ""

info "Step 5: Installing RTL-SDR drivers..."
confirm "Proceed with installation?" || { error "Cannot proceed without installing drivers — aborting."; }

sudo make install
sudo cp "$CLONE_DIR/rtl-sdr.rules" /etc/udev/rules.d/
sudo ldconfig

info "Drivers installed and ldconfig updated."
echo ""

# -----------------------------------------------------------------------------
# Step 5 — Blacklist DVB-T kernel module
# -----------------------------------------------------------------------------
info "Step 6: Blacklisting DVB-T kernel module..."

BLACKLIST_FILE="/etc/modprobe.d/blacklist-dvb_usb_rtl28xxu.conf"
BLACKLIST_ENTRY="blacklist dvb_usb_rtl28xxu"

if [ -f "$BLACKLIST_FILE" ] && grep -q "$BLACKLIST_ENTRY" "$BLACKLIST_FILE"; then
    info "DVB-T module already blacklisted — skipping."
else
    echo "$BLACKLIST_ENTRY" | sudo tee --append "$BLACKLIST_FILE"
    info "DVB-T module blacklisted at $BLACKLIST_FILE."
fi
echo ""

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo "============================================="
info "RTL-SDR driver setup complete!"
echo ""
echo "  Drivers    : Osmocom rtl-sdr (built from source)"
echo "  udev rules : /etc/udev/rules.d/rtl-sdr.rules"
echo "  Blacklist  : $BLACKLIST_FILE"
echo ""
warn "A reboot is required to apply the kernel module blacklist."
echo ""
confirm "Reboot now?" && sudo reboot || warn "Remember to reboot before connecting the RTL-SDR dongle."
echo "============================================="
