#!/bin/bash
# =============================================================================
# APRS Deployment Script
# Deploys APRS systemd services and applies database migration
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CURRENT_USER=$(whoami)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo "============================================"
echo "   APRS Deployment Script"
echo "============================================"
echo ""

# Check we're in the right place
if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    error "Cannot find docker-compose.yml - are you in the right directory?"
fi

# -----------------------------------------------------------------------------
# Deploy systemd services
# -----------------------------------------------------------------------------
info "Deploying systemd services..."

SERVICE_DIR="$SCRIPT_DIR"

if [ ! -f "$SERVICE_DIR/aprs-receiver.service" ]; then
    error "Cannot find aprs-receiver.service at $SERVICE_DIR"
fi

if [ ! -f "$SERVICE_DIR/aprs-bridge.service" ]; then
    error "Cannot find aprs-bridge.service at $SERVICE_DIR"
fi

# Copy services to systemd directory
sudo cp "$SERVICE_DIR/aprs-receiver.service" /etc/systemd/system/
sudo cp "$SERVICE_DIR/aprs-bridge.service" /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

info "Systemd services deployed"

# -----------------------------------------------------------------------------
# Apply database migration
# -----------------------------------------------------------------------------
info "Applying APRS database migration..."

MIGRATION_FILE="$PROJECT_ROOT/backend/geotracker/migrations/aprs_functions.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    error "Cannot find migration file at $MIGRATION_FILE"
fi

# Check if database container is running
if ! docker ps | grep -q carputer_db; then
    error "PostgreSQL container is not running. Start it with: docker compose up -d"
fi

# Apply migration
docker exec -i carputer_db psql -U postgres carputer < "$MIGRATION_FILE"

# Verify schema exists
docker exec carputer_db psql -U postgres carputer -c "\dn aprs" | grep -q aprs && \
    info "APRS schema created successfully" || \
    error "APRS schema creation failed"

info "Database migration complete"

# -----------------------------------------------------------------------------
# Enable services (don't start yet - wait for user)
# -----------------------------------------------------------------------------
info "Enabling APRS services..."

sudo systemctl enable aprs-receiver
sudo systemctl enable aprs-bridge

info "APRS services enabled (will start on boot)"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
echo "============================================"
info "APRS deployment complete!"
echo ""
echo "Services deployed:"
echo "  - /etc/systemd/system/aprs-receiver.service"
echo "  - /etc/systemd/system/aprs-bridge.service"
echo ""
echo "Database:"
echo "  - aprs schema created"
echo "  - aprs.stations table ready"
echo "  - aprs.packet_history table ready"
echo ""
warn "Next steps:"
warn "  1. Rebuild API: cd $PROJECT_ROOT && docker compose build api"
warn "  2. Restart API: docker compose restart api"
warn "  3. Start APRS services: sudo systemctl start aprs-receiver aprs-bridge"
warn "  4. Check logs: sudo journalctl -u aprs-receiver -f"
echo "============================================"
