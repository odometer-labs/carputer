#!/bin/bash
# Carputer Demo Script
# Starts all services with mock GPS and APRS data for demonstration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  Carputer Demo"
echo "========================================="
echo ""

# Change to project directory
cd "$PROJECT_DIR"

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker first."
    exit 1
fi

# Start docker compose services (without tile server to save memory)
echo "[1/3] Starting Docker services..."
docker compose up -d db api core-api frontend gpsd-service sys-health

# Wait for services to be healthy
echo "[2/3] Waiting for services to be healthy..."
sleep 5

# Check if Python venv exists, create if not
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate venv and install dependencies
source .venv/bin/activate
pip install -q requests 2>/dev/null || true

# Start mock GPS in background
echo "[3/3] Starting mock GPS and APRS..."
cd embedded

# Kill any existing mock processes
pkill -f "gpsd_mock" 2>/dev/null || true
pkill -f "aprs_mock" 2>/dev/null || true

# Start mock GPS
python3 -m gpsd_mock --speed 8.0 &
GPS_PID=$!
echo "  Mock GPS started (PID: $GPS_PID)"

# Wait a moment for GPS to start
sleep 2

# Start mock APRS stations
python3 aprs_mock/mock_stations.py &
APRS_PID=$!
echo "  Mock APRS started (PID: $APRS_PID)"

echo ""
echo "========================================="
echo "  Demo Running!"
echo "========================================="
echo ""
echo "  Open http://localhost:3000 in your browser"
echo ""
echo "  Mock GPS: Driving around PSU campus"
echo "  Mock APRS: 6 stations near downtown Portland"
echo ""
echo "  Press Ctrl+C to stop the demo"
echo ""

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    echo "Stopping demo..."
    kill $GPS_PID 2>/dev/null || true
    kill $APRS_PID 2>/dev/null || true
    echo "Demo stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
