#!/bin/bash
# =============================================================================
# Odometer Labs — Carputer Pi Setup Script
# =============================================================================
# Usage: bash script.sh
# Run this script on a fresh Raspberry Pi OS Lite (64-bit) install.
# Idempotent — safe to run multiple times.
#
# Prerequisites:
#   - Raspberry Pi OS Lite (64-bit) flashed and booted
#   - SSH access established
#   - Internet connection available
#   - u-blox C099-F9P connected via USB-C cable
#   - RTL-SDR USB dongle connected (for APRS reception)
#
# What this script does:
#    1. Installs required packages
#    2. Installs Docker and adds user to docker group
#    3. Clones the carputer repo to /opt/carputer
#    4. Configures gpsd for u-blox GPS module
#    5. Installs RTL-SDR drivers and blacklists conflicting modules
#    6. Builds and installs Direwolf (APRS decoder)
#    7. Deploys chrony GPS time discipline config and gpsd drop-in
#    8. Deploys carputer.service
#    9. Configures APRS reception (Direwolf + RTL-SDR pipeline)
#   10. Deploys APRS bridge from embedded/aprs_bridge
#   11. Deploys APRS systemd services
#   12. Enables system services
#   13. Sets up Docker environment and builds containers
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Colors
# -----------------------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
REPO_URL="https://github.com/odometer-labs/carputer.git"
DEPLOY_DIR="/opt/carputer"
APRS_DIR="$DEPLOY_DIR/aprs"
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

sudo apt update
sudo apt install -y vim git gpsd gpsd-clients chrony curl \
    rtl-sdr cmake gcc g++ make libasound2-dev \
    python3-requests python3-pip

info "Packages installed successfully."
echo ""

# -----------------------------------------------------------------------------
# Step 2 — Install Docker
# -----------------------------------------------------------------------------
info "Step 2: Installing Docker and plugins..."

ARCH=$(uname -m)
case "$ARCH" in
    aarch64) COMPOSE_ARCH="linux-aarch64"; BUILDX_ARCH="linux-arm64" ;;
    x86_64)  COMPOSE_ARCH="linux-x86_64";  BUILDX_ARCH="linux-amd64" ;;
    armv7l)  COMPOSE_ARCH="linux-armv7";   BUILDX_ARCH="linux-armv7" ;;
    *)       COMPOSE_ARCH="linux-x86_64";  BUILDX_ARCH="linux-amd64" ;;
esac
info "Detected architecture: $ARCH (Compose: $COMPOSE_ARCH, Buildx: $BUILDX_ARCH)"

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

sudo mkdir -p /usr/local/lib/docker/cli-plugins

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

if grep -q "DOCKER_BUILDKIT=1" /etc/environment 2>/dev/null; then
    info "BuildKit is already enabled."
else
    info "Enabling BuildKit by default..."
    echo 'DOCKER_BUILDKIT=1' | sudo tee -a /etc/environment > /dev/null
    export DOCKER_BUILDKIT=1
    info "BuildKit enabled."
fi

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

if systemctl is-enabled docker &>/dev/null; then
    info "Docker is already enabled to start on boot."
else
    sudo systemctl enable docker
    sudo systemctl start docker
    info "Docker enabled and started."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 3 — Clone repo to /opt/carputer
# -----------------------------------------------------------------------------
info "Step 3: Setting up carputer repository at $DEPLOY_DIR..."

if [ -d "$DEPLOY_DIR/.git" ]; then
    info "Repository already exists at $DEPLOY_DIR."
    if confirm "Pull latest changes?"; then
        sudo git -C "$DEPLOY_DIR" pull
        info "Repository updated."
    fi
else
    sudo mkdir -p "$DEPLOY_DIR"
    sudo git clone "$REPO_URL" "$DEPLOY_DIR"
    sudo chown -R "$CURRENT_USER":"$CURRENT_USER" "$DEPLOY_DIR"
    info "Repository cloned to $DEPLOY_DIR."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 4 — Configure gpsd
# -----------------------------------------------------------------------------
info "Step 4: Configuring gpsd..."

GPSD_CONFIG="/etc/default/gpsd"

if grep -q 'DEVICES="/dev/ttyACM0"' "$GPSD_CONFIG" 2>/dev/null && \
   grep -q 'GPSD_OPTIONS="-n"' "$GPSD_CONFIG" 2>/dev/null && \
   grep -q 'START_DAEMON="true"' "$GPSD_CONFIG" 2>/dev/null; then
    info "gpsd is already configured."
else
    if confirm "Configure gpsd for /dev/ttyACM0?"; then
        sudo cp "$GPSD_CONFIG" "$GPSD_CONFIG.bak" 2>/dev/null || true
        sudo tee "$GPSD_CONFIG" > /dev/null <<'EOF'
# Default settings for gpsd
START_DAEMON="true"
DEVICES="/dev/ttyACM0"
GPSD_OPTIONS="-n"
USBAUTO="false"
EOF
        info "gpsd configured for /dev/ttyACM0 (backup at $GPSD_CONFIG.bak)."
    else
        warn "Skipping gpsd configuration."
    fi
fi
echo ""

# -----------------------------------------------------------------------------
# Step 5 — Configure RTL-SDR and blacklist conflicting drivers
# -----------------------------------------------------------------------------
info "Step 5: Configuring RTL-SDR..."

BLACKLIST_FILE="/etc/modprobe.d/blacklist-rtl.conf"

if [ -f "$BLACKLIST_FILE" ]; then
    info "RTL-SDR blacklist already exists at $BLACKLIST_FILE."
else
    sudo tee "$BLACKLIST_FILE" > /dev/null <<'EOF'
# Blacklist DVB-T drivers that conflict with RTL-SDR
blacklist dvb_usb_rtl28xxu
blacklist rtl2832
blacklist rtl2830
EOF
    info "RTL-SDR blacklist created at $BLACKLIST_FILE."
    sudo rmmod dvb_usb_rtl28xxu 2>/dev/null || true
    sudo rmmod rtl2832 2>/dev/null || true
    sudo rmmod rtl2830 2>/dev/null || true
    warn "Conflicting modules unloaded. A reboot is recommended."
fi

if groups "$CURRENT_USER" | grep -q '\bplugdev\b'; then
    info "User $CURRENT_USER is already in the plugdev group."
else
    sudo usermod -aG plugdev "$CURRENT_USER"
    info "User $CURRENT_USER added to plugdev group."
    warn "You must log out and back in for this to take effect."
fi

if lsusb | grep -qi rtl; then
    info "RTL-SDR device detected via USB."
else
    warn "RTL-SDR device not detected. Ensure dongle is connected."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 6 — Build and install Direwolf
# -----------------------------------------------------------------------------
info "Step 6: Building and installing Direwolf..."

DIREWOLF_DIR="$HOME/direwolf"
BUILD_DIREWOLF=true

if command -v direwolf &>/dev/null; then
    DIREWOLF_VERSION=$(direwolf -v 2>&1 | head -1 || echo "installed")
    info "Direwolf is already installed ($DIREWOLF_VERSION)."
    confirm "Rebuild Direwolf from latest source?" || BUILD_DIREWOLF=false
fi

if $BUILD_DIREWOLF; then
    if [ ! -d "$DIREWOLF_DIR" ]; then
        info "Cloning Direwolf repository..."
        git clone https://github.com/wb2osz/direwolf "$DIREWOLF_DIR"
    else
        info "Direwolf repository already exists at $DIREWOLF_DIR."
        confirm "Pull latest changes?" && git -C "$DIREWOLF_DIR" pull || true
    fi

    info "Building Direwolf (this may take 5-10 minutes)..."
    (
        cd "$DIREWOLF_DIR"
        mkdir -p build
        cd build
        cmake ..
        make -j4
        sudo make install
        sudo make install-conf
    )
    info "Direwolf installed successfully."
else
    info "Skipping Direwolf build."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 7 — Deploy chrony config and gpsd drop-in
# -----------------------------------------------------------------------------
info "Step 7: Deploying chrony + GPSD time sync configuration..."

CHRONY_SRC="$DEPLOY_DIR/embedded/ntp_gps_sync/chrony.conf"
CHRONY_DST="/etc/chrony/chrony.conf"
GPSD_DROPIN_SRC="$DEPLOY_DIR/embedded/ntp_gps_sync/gpsd-depends-chrony.conf"
GPSD_DROPIN_DIR="/etc/systemd/system/gpsd.service.d"
GPSD_DROPIN_DST="$GPSD_DROPIN_DIR/depends-chrony.conf"

if [ -f "$CHRONY_SRC" ]; then
    if diff -q "$CHRONY_SRC" "$CHRONY_DST" &>/dev/null; then
        info "chrony.conf is already up to date."
    else
        if confirm "Deploy GPS-disciplined chrony.conf?"; then
            sudo cp "$CHRONY_DST" "$CHRONY_DST.bak" 2>/dev/null || true
            sudo cp "$CHRONY_SRC" "$CHRONY_DST"
            info "chrony.conf deployed (backup at $CHRONY_DST.bak)."
        else
            warn "Skipping chrony config."
        fi
    fi
else
    warn "chrony.conf not found at $CHRONY_SRC — skipping."
fi

if [ -f "$GPSD_DROPIN_SRC" ]; then
    sudo mkdir -p "$GPSD_DROPIN_DIR"
    if diff -q "$GPSD_DROPIN_SRC" "$GPSD_DROPIN_DST" &>/dev/null; then
        info "gpsd drop-in already up to date."
    else
        if confirm "Deploy gpsd drop-in?"; then
            sudo cp "$GPSD_DROPIN_SRC" "$GPSD_DROPIN_DST"
            sudo systemctl daemon-reload
            info "gpsd drop-in deployed."
        else
            warn "Skipping gpsd drop-in."
        fi
    fi
else
    warn "gpsd drop-in not found at $GPSD_DROPIN_SRC — skipping."
fi

if systemctl is-active chrony &>/dev/null; then
    sudo systemctl restart chrony
    info "chrony restarted."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 8 — Deploy carputer.service
# -----------------------------------------------------------------------------
info "Step 8: Deploying carputer.service..."

SERVICE_SRC="$DEPLOY_DIR/infrastructure/systemd/carputer.service"
SERVICE_DST="/etc/systemd/system/carputer.service"

if [ ! -f "$SERVICE_SRC" ]; then
    warn "carputer.service not found at $SERVICE_SRC — skipping."
else
    if diff -q "$SERVICE_SRC" "$SERVICE_DST" &>/dev/null; then
        info "carputer.service is already up to date."
    else
        if confirm "Deploy carputer.service?"; then
            sudo cp "$SERVICE_SRC" "$SERVICE_DST"
            sudo systemctl daemon-reload
            sudo systemctl enable carputer
            info "carputer.service deployed and enabled."
        else
            warn "Skipping carputer.service deployment."
        fi
    fi
fi
echo ""

# -----------------------------------------------------------------------------
# Step 9 — Configure APRS reception
# -----------------------------------------------------------------------------
info "Step 9: Configuring APRS reception..."

sudo mkdir -p "$APRS_DIR"
sudo mkdir -p /var/log/carputer/aprs
sudo chown -R "$CURRENT_USER":"$CURRENT_USER" "$APRS_DIR"
sudo chown -R "$CURRENT_USER":"$CURRENT_USER" /var/log/carputer

DIREWOLF_CONF="$APRS_DIR/direwolf.conf"
WRITE_DIREWOLF_CONF=true

if [ -f "$DIREWOLF_CONF" ]; then
    info "Direwolf config already exists at $DIREWOLF_CONF."
    confirm "Overwrite with default config?" || WRITE_DIREWOLF_CONF=false
fi

if $WRITE_DIREWOLF_CONF; then
    cat > "$DIREWOLF_CONF" <<'EOF'
#############################################################
# Direwolf Configuration for APRS Reception
# Raspberry Pi Carputer Project
#############################################################

# Audio device — pipe audio from rtl_fm
ADEVICE stdin null

# Channel 0: APRS 1200 baud AFSK
CHANNEL 0
MYCALL N0CALL-10
MODEM 1200

QUIET

# KISS interface on TCP port 8003
KISSPORT 8003

# AGW port on 8005 (avoids overlap with :8000)
AGWPORT 8005

LOGDIR /var/log/carputer/aprs
LOGFILE aprs-%Y%m%d.log

# Receive all packets
FILTER 0 1

# Receive-only — no license required
DIGIPEAT 0 0
EOF
    info "Direwolf configuration written to $DIREWOLF_CONF."
else
    warn "Keeping existing Direwolf config."
fi

APRS_SCRIPT="$APRS_DIR/start_aprs.sh"
cat > "$APRS_SCRIPT" <<'EOF'
#!/bin/bash
# APRS Reception Pipeline: RTL-SDR → rtl_fm → Direwolf
FREQ=144390000
DEVICE=0
SAMPLE_RATE=24000
mkdir -p /var/log/carputer/aprs
echo "Starting APRS reception on 144.390 MHz..."
rtl_fm -f $FREQ -s $SAMPLE_RATE -g 49.6 -p 0 -d $DEVICE - | \
    direwolf -c /opt/carputer/aprs/direwolf.conf -r $SAMPLE_RATE -D 1 -
EOF
chmod +x "$APRS_SCRIPT"
info "APRS reception script written to $APRS_SCRIPT."
echo ""

# -----------------------------------------------------------------------------
# Step 10 — Deploy APRS bridge
# -----------------------------------------------------------------------------
info "Step 10: Deploying APRS bridge from embedded/aprs_bridge..."

APRS_BRIDGE_DIR="$APRS_DIR/aprs_bridge"

if [ -d "$APRS_BRIDGE_DIR" ]; then
    info "APRS bridge already exists at $APRS_BRIDGE_DIR."
    if confirm "Overwrite with latest from repo?"; then
        rm -rf "$APRS_BRIDGE_DIR"
        cp -r "$DEPLOY_DIR/embedded/aprs_bridge" "$APRS_DIR/"
        info "APRS bridge updated at $APRS_BRIDGE_DIR."
    else
        warn "Skipping APRS bridge update."
    fi
else
    cp -r "$DEPLOY_DIR/embedded/aprs_bridge" "$APRS_DIR/"
    info "APRS bridge deployed to $APRS_BRIDGE_DIR."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 11 — Deploy APRS systemd services
# -----------------------------------------------------------------------------
info "Step 11: Deploying APRS systemd services..."

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
WorkingDirectory=$APRS_DIR
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
info "APRS receiver service deployed."

APRS_BRIDGE_SERVICE="/etc/systemd/system/aprs-bridge.service"
sudo tee "$APRS_BRIDGE_SERVICE" > /dev/null <<EOF
[Unit]
Description=APRS Bridge to Backend
After=aprs-receiver.service network.target
Requires=aprs-receiver.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$APRS_DIR
Environment="KISS_HOST=localhost"
Environment="KISS_PORT=8003"
Environment="AGW_HOST=localhost"
Environment="AGW_PORT=8005"
Environment="BACKEND_URL=http://localhost:8000"
ExecStart=/usr/bin/python3 -m aprs_bridge
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aprs-bridge

[Install]
WantedBy=multi-user.target
EOF
info "APRS bridge service deployed."

sudo systemctl daemon-reload
sudo systemctl enable aprs-receiver
sudo systemctl enable aprs-bridge
info "APRS services enabled to start on boot."
echo ""

# -----------------------------------------------------------------------------
# Step 12 — Enable system services
# -----------------------------------------------------------------------------
info "Step 12: Enabling system services..."

if systemctl is-enabled chrony &>/dev/null; then
    info "chrony is already enabled."
else
    sudo systemctl enable chrony
    sudo systemctl start chrony
    info "chrony enabled and started."
fi

if systemctl is-enabled gpsd &>/dev/null; then
    info "gpsd is already enabled."
else
    sudo systemctl enable gpsd
    sudo systemctl start gpsd
    info "gpsd enabled and started."
fi

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
# Step 13 — Set up Docker environment and build containers
# -----------------------------------------------------------------------------
info "Step 13: Setting up Docker environment..."

ENV_EXAMPLE="$DEPLOY_DIR/.env.example"
ENV_FILE="$DEPLOY_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    info ".env file already exists."
elif [ -f "$ENV_EXAMPLE" ]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    info ".env file created from .env.example."
    warn "Edit $ENV_FILE to set your database credentials before starting containers."
else
    warn ".env.example not found — skipping .env setup."
fi

if command -v docker &>/dev/null && [ -f "$ENV_FILE" ]; then
    cd "$DEPLOY_DIR"
    info "Building Docker containers..."
    docker compose build
    info "Docker containers built."
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
echo "  Direwolf KISS : localhost:8003"
echo "  Direwolf AGW  : localhost:8005"
echo "  Repo          : $DEPLOY_DIR"
echo ""
echo "  Services enabled:"
echo "    ✓ chrony (GPS time sync)"
echo "    ✓ gpsd (GPS daemon)"
echo "    ✓ docker (container runtime)"
echo "    ✓ carputer (auto-start on boot)"
echo "    ✓ aprs-receiver (RTL-SDR + Direwolf)"
echo "    ✓ aprs-bridge (KISS → Backend)"
echo ""
echo "  Docker services (start with: cd $DEPLOY_DIR && docker compose up -d):"
echo "    • Frontend: http://localhost:3000"
echo "    • API:      http://localhost:8000"
echo "    • Swagger:  http://localhost:8000/docs"
echo "    • Adminer:  http://localhost:8080"
echo ""
warn "NEXT STEPS:"
warn "  1. Edit $DEPLOY_DIR/.env with your credentials"
warn "  2. Start containers: cd $DEPLOY_DIR && docker compose up -d"
warn "  3. Test GPS: cgps -s"
warn "  4. Start APRS: sudo systemctl start aprs-receiver aprs-bridge"
warn "  5. Test APRS: sudo journalctl -u aprs-receiver -f"
warn "  6. Check logs: tail -f /var/log/carputer/aprs/aprs-*.log"
echo ""
warn "REBOOT RECOMMENDED to load RTL-SDR driver and group changes."
echo "=================================================================="
