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
#   6. Configures APRS reception pipeline
#   7. Creates APRS bridge to backend
#   8. Enables and starts required systemd services
#   9. Clones the carputer repo to /opt/carputer
#  10. Deploys chrony GPS time discipline config and gpsd drop-in
#  11. Deploys carputer.service
#  12. Sets up Docker environment (.env) and pulls containers
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
APRS_DIR="/opt/carputer/aprs"
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
echo "=================================================================="
echo "   Odometer Labs — Carputer Pi Setup Script (with APRS Support)  "
echo "=================================================================="
echo ""
warn "This script will install packages and modify system configuration."
warn "Ensure the u-blox C099-F9P is connected via USB-C cable."
warn "Ensure the RTL-SDR USB dongle is connected (for APRS reception)."
echo ""
confirm "Do you want to proceed?" || { echo "Aborted."; exit 0; }
echo ""

# -----------------------------------------------------------------------------
# Step 1 — System update and package installation
# -----------------------------------------------------------------------------
info "Step 1: Installing required packages..."
info "  Base: vim, git, curl"
info "  GPS: gpsd, gpsd-clients, chrony"
info "  RTL-SDR: rtl-sdr"
info "  Direwolf deps: cmake, gcc, g++, make, libasound2-dev"
info "  Python: python3-requests"
echo ""
confirm "Proceed with package installation?" || { warn "Skipping package installation."; }

sudo apt update
sudo apt install -y vim git gpsd gpsd-clients chrony curl \
    rtl-sdr cmake gcc g++ make libasound2-dev \
    python3-requests python3-pip

info "Packages installed successfully."

echo ""

# ----------------------------------------------------------------------------
# Step 2— Install Docker
# ----------------------------------------------------------------------------
info "Step 2: Installing Docker and plugins..."

# Detect architecture for plugin downloads
# Note: Compose and Buildx use different arch naming conventions
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
    if confirm "Install Docker using the official convenience script?"; then
        info "Downloading and running Docker install script..."
        curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
        sudo sh /tmp/get-docker.sh
        rm /tmp/get-docker.sh
        info "Docker installed successfully."
    else
        warn "Skipping Docker installation."
    fi
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
    if confirm "Add $CURRENT_USER to the docker group (run docker without sudo)?"; then
        sudo usermod -aG docker "$CURRENT_USER"
        info "User $CURRENT_USER added to docker group."
        warn "You must log out and back in (or run 'newgrp docker') for this to take effect."
    else
        warn "Skipping docker group."
    fi
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
   grep -q 'GPSD_OPTIONS="-G -F /var/run/gpsd.sock"' "$GPSD_CONFIG"; then
    info "gpsd is already configured correctly — skipping."
else
    if confirm "Update $GPSD_CONFIG with correct DEVICES and GPSD_OPTIONS?"; then
        sudo sed -i 's|^DEVICES=.*|DEVICES="/dev/ttyACM0"|' "$GPSD_CONFIG"
        sudo sed -i 's|^GPSD_OPTIONS=.*|GPSD_OPTIONS="-G -F /var/run/gpsd.sock"|' "$GPSD_CONFIG"
        info "gpsd configuration updated:"
        info "  DEVICES=/dev/ttyACM0"
        info "  GPSD_OPTIONS=-G -F /var/run/gpsd.sock"
    else
        warn "Skipping gpsd config."
    fi
fi
echo ""

# Deploy gpsd.socket override to allow remote access (needed for Docker containers)
GPSD_SOCKET_DROPIN_DIR="/etc/systemd/system/gpsd.socket.d"
GPSD_SOCKET_DROPIN="$GPSD_SOCKET_DROPIN_DIR/listen-all.conf"
GPSD_SOCKET_CONTENT="[Socket]
# Clear inherited ListenStream, then re-declare with remote access enabled
ListenStream=
ListenStream=/run/gpsd.sock
ListenStream=0.0.0.0:2947
ListenStream=[::]:2947
BindIPv6Only=ipv6-only"

if [ -f "$GPSD_SOCKET_DROPIN" ] && echo "$GPSD_SOCKET_CONTENT" | diff -q - "$GPSD_SOCKET_DROPIN" &>/dev/null; then
    info "gpsd.socket remote access override already up to date - skipping."
else
    if confirm "Deploy gpsd.socket override to allow remote access (required for Docker)?"; then
        sudo mkdir -p "$GPSD_SOCKET_DROPIN_DIR"
        echo "$GPSD_SOCKET_CONTENT" | sudo tee "$GPSD_SOCKET_DROPIN" > /dev/null
        sudo systemctl daemon-reload
        info "gpsd.socket override deployed at $GPSD_SOCKET_DROPIN."
        info "  gpsd now accepts connections on all interfaces (0.0.0.0:2947)."
    else
        warn "Skipping gpsd.socket override."
    fi
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
    confirm "Create RTL-SDR driver blacklist (prevents DVB-T conflicts)?" || { warn "Skipping RTL-SDR blacklist."; }

    sudo tee "$BLACKLIST_FILE" > /dev/null <<'EOF'
# Blacklist DVB-T drivers that conflict with RTL-SDR
blacklist dvb_usb_rtl28xxu
blacklist rtl2832
blacklist rtl2830
EOF

    info "RTL-SDR blacklist created at $BLACKLIST_FILE."
    
    # Unload conflicting modules if currently loaded
    sudo rmmod dvb_usb_rtl28xxu 2>/dev/null || true
    sudo rmmod rtl2832 2>/dev/null || true
    sudo rmmod rtl2830 2>/dev/null || true
    
    warn "Conflicting modules unloaded. A reboot is recommended."
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
info "Step 5: Building and installing Direwolf..."

# Check if Direwolf is already installed
if command -v direwolf &>/dev/null; then
    DIREWOLF_VERSION=$(direwolf -v 2>&1 | head -1 || echo "installed")
    info "Direwolf is already installed ($DIREWOLF_VERSION)."
    confirm "Rebuild Direwolf from latest source?" || { warn "Skipping Direwolf build."; }
fi

# Clone and build Direwolf
DIREWOLF_DIR="$HOME/direwolf"

if [ ! -d "$DIREWOLF_DIR" ]; then
    info "Cloning Direwolf repository..."
    git clone https://github.com/wb2osz/direwolf "$DIREWOLF_DIR"
else
    info "Direwolf repository already exists at $DIREWOLF_DIR."
    confirm "Pull latest changes?" && git -C "$DIREWOLF_DIR" pull
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

# -----------------------------------------------------------------------------
# Step 6 — Configure APRS reception
# -----------------------------------------------------------------------------
info "Step 6: Configuring APRS reception..."

# Create APRS directory
sudo mkdir -p "$APRS_DIR"
sudo mkdir -p /var/log/carputer/aprs
sudo chown -R "$CURRENT_USER":"$CURRENT_USER" "$APRS_DIR"
sudo chown -R "$CURRENT_USER":"$CURRENT_USER" /var/log/carputer

# Deploy Direwolf configuration
DIREWOLF_CONF="$APRS_DIR/direwolf.conf"

if [ -f "$DIREWOLF_CONF" ]; then
    info "Direwolf config already exists at $DIREWOLF_CONF."
    confirm "Overwrite with default config?" || { warn "Skipping Direwolf config."; }
fi

info "Creating Direwolf configuration..."
cat > "$DIREWOLF_CONF" <<'EOF'
#############################################################
# Direwolf Configuration for APRS Reception
# Raspberry Pi Carputer Project
#############################################################

# Audio device - we'll pipe audio from rtl_fm
ADEVICE stdin null

# Channel 0: APRS 1200 baud AFSK
CHANNEL 0
MYCALL N0CALL-10
MODEM 1200

# Reduce console spam
QUIET

# Enable KISS interface on TCP port 8001
KISSPORT 8001

# Log all received packets
LOGDIR /var/log/carputer/aprs
LOGFILE aprs-%Y%m%d.log

# Receive all packets (no filtering)
FILTER 0 1

# Digipeater DISABLED (receive-only, no license needed)
DIGIPEAT 0 0

# Internet gateway DISABLED (receive-only)
# Don't connect to APRS-IS network

# Beaconing DISABLED (receive-only, no license needed)
EOF

info "Direwolf configuration created at $DIREWOLF_CONF."

# Deploy APRS reception script
APRS_SCRIPT="$APRS_DIR/start_aprs.sh"

info "Creating APRS reception script..."
cat > "$APRS_SCRIPT" <<'EOF'
#!/bin/bash
#############################################################
# APRS Reception Pipeline
# RTL-SDR → rtl_fm → Direwolf
#############################################################

# APRS frequency for North America: 144.390 MHz
FREQ=144390000  # Hz

# RTL-SDR device (usually 0)
DEVICE=0

# Sample rate (24000 Hz is good for APRS)
SAMPLE_RATE=24000

# Create log directory
mkdir -p /var/log/carputer/aprs

# Start pipeline
echo "Starting APRS reception on 144.390 MHz..."

# rtl_fm demodulates FM audio, pipes to Direwolf
rtl_fm -f $FREQ -s $SAMPLE_RATE -g 49.6 -p 0 -d $DEVICE - | \
    direwolf -c /opt/carputer/aprs/direwolf.conf -r $SAMPLE_RATE -D 1 -
EOF

chmod +x "$APRS_SCRIPT"
info "APRS reception script created at $APRS_SCRIPT."
echo ""

# -----------------------------------------------------------------------------
# Step 7 — Deploy APRS bridge to backend
# -----------------------------------------------------------------------------
info "Step 7: Creating APRS bridge to backend..."

APRS_BRIDGE="$APRS_DIR/aprs_bridge.py"

cat > "$APRS_BRIDGE" <<'PYEOF'
#!/usr/bin/env python3
"""
APRS Bridge - Connects Direwolf to FastAPI Backend
Reads APRS packets from Direwolf KISS interface (TCP port 8001)
Sends to backend API for storage in PostgreSQL
"""

import socket
import json
import time
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='/var/log/carputer/aprs-bridge.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
KISS_HOST = 'localhost'
KISS_PORT = 8001
BACKEND_URL = 'http://localhost:8000/api/aprs/ingest'

def parse_kiss_frame(frame):
    """Parse KISS frame from Direwolf"""
    try:
        FEND = 0xC0
        if frame[0] == FEND:
            frame = frame[1:]
        if frame[-1] == FEND:
            frame = frame[:-1]
        if frame[0] == 0x00:
            frame = frame[1:]
        
        packet_str = frame.decode('latin-1', errors='ignore')
        return packet_str
    except Exception as e:
        logging.error(f"Failed to parse KISS frame: {e}")
        return None

def parse_aprs_packet(packet_str):
    """Parse APRS packet string"""
    try:
        if '>' not in packet_str or ':' not in packet_str:
            return None
        
        callsign = packet_str.split('>')[0].strip()
        data = packet_str.split(':', 1)[1] if ':' in packet_str else ''
        
        return {
            'callsign': callsign,
            'raw_packet': packet_str,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
    except Exception as e:
        logging.error(f"Failed to parse APRS packet: {e}")
        return None

def send_to_backend(packet_data):
    """Send parsed APRS packet to backend API"""
    try:
        response = requests.post(
            BACKEND_URL,
            json=packet_data,
            timeout=5
        )
        
        if response.status_code == 200:
            logging.info(f"Sent APRS packet from {packet_data.get('callsign', 'unknown')}")
        else:
            logging.warning(f"Backend returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send to backend: {e}")

def main():
    """Main APRS bridge loop"""
    logging.info("Starting APRS bridge...")
    
    while True:
        try:
            logging.info(f"Connecting to Direwolf at {KISS_HOST}:{KISS_PORT}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((KISS_HOST, KISS_PORT))
            logging.info("Connected to Direwolf KISS interface")
            
            buffer = b''
            FEND = 0xC0
            
            while True:
                data = sock.recv(4096)
                if not data:
                    logging.warning("KISS connection closed")
                    break
                
                buffer += data
                
                while True:
                    start = buffer.find(bytes([FEND]))
                    if start == -1:
                        break
                    
                    end = buffer.find(bytes([FEND]), start + 1)
                    if end == -1:
                        break
                    
                    frame = buffer[start:end+1]
                    buffer = buffer[end+1:]
                    
                    packet_str = parse_kiss_frame(frame)
                    if packet_str:
                        packet_data = parse_aprs_packet(packet_str)
                        if packet_data:
                            send_to_backend(packet_data)
            
            sock.close()
        except ConnectionRefusedError:
            logging.error("Cannot connect to Direwolf - is it running?")
            time.sleep(10)
        except Exception as e:
            logging.error(f"APRS bridge error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
PYEOF

chmod +x "$APRS_BRIDGE"
info "APRS bridge created at $APRS_BRIDGE."
echo ""

# -----------------------------------------------------------------------------
# Step 8 — Deploy systemd services for APRS
# -----------------------------------------------------------------------------
info "Step 8: Deploying APRS systemd services..."

# APRS receiver service
APRS_RECEIVER_SERVICE="/etc/systemd/system/aprs-receiver.service"

sudo tee "$APRS_RECEIVER_SERVICE" > /dev/null <<EOF
[Unit]
Description=APRS Receiver (RTL-SDR + Direwolf)
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=plugdev
WorkingDir=$APRS_DIR
ExecStartPre=/bin/sleep 5
ExecStart=$APRS_DIR/start_aprs.sh
Restart=on-failure
RestartSec=10
Nice=-5
CPUQuota=50%
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aprs-receiver

[Install]
WantedBy=multi-user.target
EOF

info "APRS receiver service created at $APRS_RECEIVER_SERVICE."

# APRS bridge service
APRS_BRIDGE_SERVICE="/etc/systemd/system/aprs-bridge.service"

sudo tee "$APRS_BRIDGE_SERVICE" > /dev/null <<EOF
[Unit]
Description=APRS Bridge to Backend
After=aprs-receiver.service network.target
Requires=aprs-receiver.service

[Service]
Type=simple
User=$CURRENT_USER
ExecStart=/usr/bin/python3 $APRS_DIR/aprs_bridge.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aprs-bridge

[Install]
WantedBy=multi-user.target
EOF

info "APRS bridge service created at $APRS_BRIDGE_SERVICE."

# Reload systemd and enable services
sudo systemctl daemon-reload

if confirm "Enable APRS services to start on boot?"; then
    sudo systemctl enable aprs-receiver
    sudo systemctl enable aprs-bridge
    info "APRS services enabled."
    
    if confirm "Start APRS services now?"; then
        sudo systemctl start aprs-receiver
        sudo systemctl start aprs-bridge
        info "APRS services started."
        info "Check status: sudo systemctl status aprs-receiver aprs-bridge"
    fi
fi
echo ""

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
if systemctl is-enabled gpsd &>/dev/null && systemctl is-active gpsd &>/dev/null; then
    info "gpsd is already enabled and running."
else
    sudo systemctl enable gpsd
    sudo systemctl start gpsd
    info "gpsd enabled and started."
fi

# postgresql — stop system postgres (Docker will provide it)
# Check for both generic 'postgresql' service and versioned 'postgresql@17-main'
if systemctl is-active postgresql &>/dev/null 2>&1; then
    warn "System PostgreSQL is running and will conflict with Docker PostgreSQL on port 5432."
    if confirm "Stop and disable system PostgreSQL? (Docker will provide PostgreSQL instead)"; then
        sudo systemctl stop postgresql
        sudo systemctl disable postgresql
        info "System PostgreSQL stopped and disabled."
    else
        warn "System PostgreSQL left running. You may need to change DB_PORT in .env."
    fi
elif systemctl is-active postgresql@17-main &>/dev/null 2>&1; then
    warn "System PostgreSQL (17-main) is running and will conflict with Docker PostgreSQL on port 5432."
    if confirm "Stop and disable system PostgreSQL? (Docker will provide PostgreSQL instead)"; then
        sudo systemctl stop postgresql@17-main
        sudo systemctl disable postgresql@17-main
        info "System PostgreSQL stopped and disabled."
    else
        warn "System PostgreSQL left running. You may need to change DB_PORT in .env."
    fi
elif systemctl is-enabled postgresql &>/dev/null 2>&1 || systemctl is-enabled postgresql@17-main &>/dev/null 2>&1; then
    info "System PostgreSQL is enabled but not running."
    if confirm "Disable system PostgreSQL to prevent future conflicts?"; then
        sudo systemctl disable postgresql 2>/dev/null || true
        sudo systemctl disable postgresql@17-main 2>/dev/null || true
        info "System PostgreSQL disabled."
    fi
else
    info "System PostgreSQL is not enabled — good, Docker will provide PostgreSQL."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 10 — Clone repo to /opt/carputer
# -----------------------------------------------------------------------------
info "Step 10: Setting up carputer repository at /opt/carputer..."

if [ -d "$DEPLOY_DIR/.git" ]; then
    info "Repository already exists at $DEPLOY_DIR."
    confirm "Pull latest changes?" && git -C "$DEPLOY_DIR" pull && info "Repository updated."
else
    if confirm "Clone $REPO_URL into $DEPLOY_DIR?"; then
        sudo mkdir -p "$DEPLOY_DIR"
        sudo git clone "$REPO_URL" "$DEPLOY_DIR"
        sudo chown -R "$CURRENT_USER":"$CURRENT_USER" "$DEPLOY_DIR"
        info "Repository cloned to $DEPLOY_DIR."
    else
        warn "Skipping repo clone."
    fi
fi
echo ""

# -----------------------------------------------------------------------------
# Step 11 — Deploy chrony config and gpsd drop-in
# -----------------------------------------------------------------------------
info "Step 11: Deploying chrony + GPSD time sync configuration..."

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
        confirm "Deploy GPS-disciplined chrony.conf?" || { warn "Skipping chrony config."; }
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
        confirm "Deploy gpsd drop-in?" || { warn "Skipping gpsd drop-in."; }
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
# Step 12 — Deploy carputer.service
# -----------------------------------------------------------------------------
info "Step 12: Deploying carputer.service..."

SERVICE_SRC="$DEPLOY_DIR/infrastructure/systemd/carputer.service"
SERVICE_DST="/etc/systemd/system/carputer.service"

if [ ! -f "$SERVICE_SRC" ]; then
    error "carputer.service not found at $SERVICE_SRC."
fi

if diff -q "$SERVICE_SRC" "$SERVICE_DST" &>/dev/null; then
    info "carputer.service is already up to date."
else
    confirm "Deploy carputer.service?" || { warn "Skipping service deployment."; }
    sudo cp "$SERVICE_SRC" "$SERVICE_DST"
    sudo systemctl daemon-reload
    sudo systemctl enable carputer
    info "carputer.service deployed and enabled."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 13 — Set up Docker environment
# -----------------------------------------------------------------------------
info "Step 13: Setting up Docker environment..."

ENV_EXAMPLE="$DEPLOY_DIR/.env.example"
ENV_FILE="$DEPLOY_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    info ".env file already exists."
else
    if [ -f "$ENV_EXAMPLE" ]; then
        confirm "Create .env from .env.example?" || { warn "Skipping .env setup."; }
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        info ".env file created at $ENV_FILE"
        warn "Edit $ENV_FILE to set your database credentials."
    else
        warn ".env.example not found — skipping .env setup."
    fi
fi

# Build and start Docker containers
if command -v docker &>/dev/null && [ -f "$ENV_FILE" ]; then
    echo ""
    if confirm "Build Docker containers now?"; then
        cd "$DEPLOY_DIR"
        info "Building Docker containers..."
        docker compose build
        info "Docker containers built."
        echo ""
        if confirm "Start Docker containers now?"; then
            docker compose up -d
            info "Docker containers started."
            info "  Frontend: http://localhost:3000"
            info "  API:      http://localhost:8000"
            info "  Docs:     http://localhost:8000/docs"
            info "  Adminer:  http://localhost:8080"
        else
            warn "Run 'docker compose up -d' when ready."
        fi
    else
        warn "Run 'cd $DEPLOY_DIR && docker compose up -d' when ready."
    fi
fi
echo ""

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo "=================================================================="
info "Setup complete!"
echo ""
echo "  GPS device    : /dev/ttyACM0"
echo "  gpsd socket   : /var/run/gpsd.sock"
echo "  RTL-SDR       : 144.390 MHz (APRS)"
echo "  Direwolf KISS : localhost:8001"
echo "  Repo          : $DEPLOY_DIR"
echo "  APRS config   : $APRS_DIR"
echo ""
echo "  Services enabled:"
echo "    ✓ chrony (GPS time sync)"
echo "    ✓ gpsd (GPS daemon)"
echo "    ✓ docker (container runtime)"
echo "    ✓ carputer (auto-start on boot)"
echo "    ✓ aprs-receiver (RTL-SDR + Direwolf)"
echo "    ✓ aprs-bridge (KISS → Backend)"
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
warn "  3. Test APRS: sudo journalctl -u aprs-receiver -f"
warn "  4. Check logs: tail -f /var/log/carputer/aprs/aprs-*.log"
warn "  5. Open frontend: http://localhost:3000"
echo ""
warn "REBOOT RECOMMENDED to load RTL-SDR driver changes."
echo "=================================================================="
