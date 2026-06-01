#!/usr/bin/env bash
# =============================================================================
# Carputer Demo Runner
# =============================================================================
# Starts the stack, wipes and re-seeds demo data, then opens both UIs.
#
# Usage:
#   ./scripts/demo_run.sh              # normal run
#   ./scripts/demo_run.sh --rebuild    # force docker image rebuild first
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

API_URL="http://localhost:8000"
CORE_API_URL="http://localhost:8888"
FRONTEND_URL="http://localhost:3000"
REMOTE_URL="http://localhost:3001"
DB_CONTAINER="carputer_db"

REBUILD=false
for arg in "$@"; do
  [[ "$arg" == "--rebuild" ]] && REBUILD=true
done

# ── colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${CYAN}[demo]${NC} $*"; }
ok()   { echo -e "${GREEN}  ✓${NC} $*"; }
warn() { echo -e "${YELLOW}  !${NC} $*"; }
die()  { echo -e "${RED}  ✗${NC} $*" >&2; exit 1; }

# ── prerequisites ─────────────────────────────────────────────────────────────
check_prereqs() {
  log "Checking prerequisites..."
  command -v docker &>/dev/null || die "docker is required but not installed."
  command -v curl   &>/dev/null || die "curl is required but not installed."
  command -v python3 &>/dev/null || die "python3 is required but not installed."
  ok "docker, curl, python3 found"
}

# ── load .env ─────────────────────────────────────────────────────────────────
load_env() {
  local env_file="$PROJECT_ROOT/.env"
  if [[ ! -f "$env_file" ]]; then
    warn ".env not found — copying from .env.example (review credentials before production use)"
    cp "$PROJECT_ROOT/.env.example" "$env_file"
  fi
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
  ok "Environment loaded (DB: ${POSTGRES_DB:-carputer})"
}

# ── start docker stack ────────────────────────────────────────────────────────
start_stack() {
  log "Starting Docker stack..."
  local compose_args=("-f" "$PROJECT_ROOT/docker-compose.yml" "up" "-d")
  [[ "$REBUILD" == true ]] && compose_args+=("--build")
  docker compose "${compose_args[@]}"
  ok "Stack started"
}

# ── wait for a service health endpoint ───────────────────────────────────────
wait_healthy() {
  local name="$1"
  local url="$2"
  local timeout_s="${3:-120}"
  local interval=3
  local elapsed=0

  log "Waiting for $name to be ready..."
  while ! curl -sf "$url" &>/dev/null; do
    if (( elapsed >= timeout_s )); then
      die "$name did not become healthy after ${timeout_s}s — check: docker compose logs"
    fi
    printf "."
    sleep "$interval"
    (( elapsed += interval ))
  done
  echo
  ok "$name is ready"
}

# ── reset demo data in the database ──────────────────────────────────────────
reset_data() {
  log "Resetting demo data..."

  # Wait briefly for the DB container to be accessible
  local retries=10
  until docker exec "$DB_CONTAINER" pg_isready -U "${POSTGRES_USER}" -q 2>/dev/null; do
    (( retries-- )) || die "DB container ($DB_CONTAINER) not ready after retries"
    sleep 2
  done

  docker exec "$DB_CONTAINER" psql \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -q \
    -c "TRUNCATE gps.aprs_stations, gps.aprs_raw_packets, gps.tracks CASCADE;" \
    2>/dev/null || die "Failed to reset demo data — is the DB running?"

  ok "APRS stations, raw packets, and tracks cleared"
}

# ── seed APRS stations and historical GPX tracks ──────────────────────────────
seed_data() {
  log "Seeding demo data..."

  if ! python3 -c "import requests" &>/dev/null; then
    warn "requests not installed — installing now"
    pip3 install -q requests
  fi

  python3 "$SCRIPT_DIR/demo_seed.py" --api "$API_URL"
}

# ── open browser tabs ─────────────────────────────────────────────────────────
open_browsers() {
  log "Opening browser tabs..."
  if command -v xdg-open &>/dev/null; then
    xdg-open "$FRONTEND_URL" 2>/dev/null &
    sleep 1
    xdg-open "$REMOTE_URL"  2>/dev/null &
  elif command -v open &>/dev/null; then   # macOS
    open "$FRONTEND_URL"
    sleep 1
    open "$REMOTE_URL"
  else
    warn "Could not detect a browser opener — open these manually:"
    echo "      In-car app:       $FRONTEND_URL"
    echo "      Remote interface: $REMOTE_URL"
    return
  fi
  ok "Browser tabs opened"
}

# ── main ──────────────────────────────────────────────────────────────────────
main() {
  echo ""
  echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${CYAN}║        Carputer Demo Runner           ║${NC}"
  echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════╝${NC}"
  echo ""

  check_prereqs
  load_env
  start_stack

  wait_healthy "Legacy API"  "$API_URL/health"
  wait_healthy "Core API"    "$CORE_API_URL/v2/root"

  reset_data
  seed_data
  open_browsers

  echo ""
  echo -e "${BOLD}${GREEN}  Demo is ready!${NC}"
  echo ""
  echo -e "  ${BOLD}In-car app:${NC}        $FRONTEND_URL"
  echo -e "  ${BOLD}Remote interface:${NC}  $REMOTE_URL"
  echo -e "  ${BOLD}API docs:${NC}          $API_URL/docs"
  echo ""
  echo -e "${CYAN}  Demo steps:${NC}"
  echo "   1. In-car app   → tap Start Track to begin recording"
  echo "   2. Watch the car drive the Portland loop — APRS stations visible on map"
  echo "   3. After a minute or two, tap Stop Track to save the recording"
  echo "   4. Remote interface → Manage Data → select track → Export GPX"
  echo ""
}

main
