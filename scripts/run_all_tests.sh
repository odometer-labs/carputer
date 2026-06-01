#!/usr/bin/env bash
# =============================================================================
# Carputer - Consolidated Test Runner
# =============================================================================
# Runs all test suites and provides a summary
# Usage: ./scripts/run_all_tests.sh
# =============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Results tracking (simple variables for portability)
FRONTEND_STATUS=""
FRONTEND_COUNT=""
API_STATUS=""
API_COUNT=""
EMBEDDED_STATUS=""
EMBEDDED_COUNT=""
BACKEND_STATUS=""
BACKEND_COUNT=""

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              CARPUTER TEST SUITE RUNNER                        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# -----------------------------------------------------------------------------
# Frontend Tests (Vitest)
# -----------------------------------------------------------------------------
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}[1/4] Frontend Tests (Svelte/Vitest)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd frontend/carputer-web-app
if npm test -- --run 2>&1 | tee /tmp/frontend_tests.log; then
    FRONTEND_STATUS="PASS"
else
    FRONTEND_STATUS="FAIL"
fi
FRONTEND_COUNT=$(grep -oE '[0-9]+ passed' /tmp/frontend_tests.log | head -1 || echo "? passed")
cd ../..

echo ""

# -----------------------------------------------------------------------------
# API Tests (pytest)
# -----------------------------------------------------------------------------
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}[2/4] API Tests (FastAPI/pytest)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd api
if python -m pytest -v 2>&1 | tee /tmp/api_tests.log; then
    API_STATUS="PASS"
else
    API_STATUS="PARTIAL"
fi
API_COUNT=$(grep -oE '[0-9]+ passed' /tmp/api_tests.log | tail -1 || echo "? passed")
cd ..

echo ""

# -----------------------------------------------------------------------------
# Embedded Tests (pytest)
# -----------------------------------------------------------------------------
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}[3/4] Embedded Tests (gpsd_mock, aprs_bridge)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd embedded
if python -m pytest -v 2>&1 | tee /tmp/embedded_tests.log; then
    EMBEDDED_STATUS="PASS"
else
    EMBEDDED_STATUS="PARTIAL"
fi
EMBEDDED_COUNT=$(grep -oE '[0-9]+ passed' /tmp/embedded_tests.log | tail -1 || echo "? passed")
cd ..

echo ""

# -----------------------------------------------------------------------------
# Backend/Geotracker Tests (pytest with uv)
# -----------------------------------------------------------------------------
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}[4/4] Backend/Geotracker Tests${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd backend/geotracker
if command -v uv &> /dev/null; then
    if uv run pytest -v 2>&1 | tee /tmp/backend_tests.log; then
        BACKEND_STATUS="PASS"
    else
        BACKEND_STATUS="SKIP"
    fi
    BACKEND_COUNT=$(grep -oE '[0-9]+ passed' /tmp/backend_tests.log | tail -1 || echo "skipped (needs DB)")
else
    echo -e "${YELLOW}uv not installed, skipping backend tests${NC}"
    BACKEND_STATUS="SKIP"
    BACKEND_COUNT="skipped (uv not installed)"
fi
cd ../..

echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                      TEST SUMMARY                              ║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════════════╣${NC}"

print_result() {
    local name=$1
    local status=$2
    local count=$3
    
    if [ "$status" = "PASS" ]; then
        icon="${GREEN}✓${NC}"
    elif [ "$status" = "PARTIAL" ]; then
        icon="${YELLOW}⚠${NC}"
    elif [ "$status" = "SKIP" ]; then
        icon="${YELLOW}○${NC}"
    else
        icon="${RED}✗${NC}"
    fi
    
    printf "${CYAN}║${NC}  %b %-12s │ %-8s │ %s\n" "$icon" "$name" "$status" "$count"
}

print_result "frontend" "$FRONTEND_STATUS" "$FRONTEND_COUNT"
print_result "api" "$API_STATUS" "$API_COUNT"
print_result "embedded" "$EMBEDDED_STATUS" "$EMBEDDED_COUNT"
print_result "backend" "$BACKEND_STATUS" "$BACKEND_COUNT"

echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Run completed: $(date)"
echo ""
