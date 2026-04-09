---
name: SYSTEM_ARCHITECTURE.md audit findings
description: Results of verifying SYSTEM_ARCHITECTURE.md against the actual codebase — 6 inaccuracies and 4 clarity issues found, not yet fixed
type: project
---

SYSTEM_ARCHITECTURE.md was audited against the live codebase on 2026-04-08. All findings were verified by reading actual source files. All fixes were applied on 2026-04-08.

**Why:** User wants to continue this work in a future session.
**How to apply:** When user asks to fix or update SYSTEM_ARCHITECTURE.md, apply all items below.

---

## Inaccuracies (factually wrong)

1. **§9 Directory Structure — `embedded/aprs/` doesn't exist**
   - Doc lists `embedded/aprs/` with `direwolf.conf`, `aprs_bridge.py`, `start_aprs.sh`
   - Actual `embedded/` contains only: `ntp_gps_sync/`, `tests/`, `pyproject.toml`, `uv.lock`
   - No `aprs/` directory exists anywhere in the repo (confirmed with glob)
   - Fix: mark the entire `embedded/aprs/` block as `[PLANNED]`

2. **§9 Directory Structure — wrong case on `ai_slop_mds/`**
   - Doc shows `ai_slop_mds/`, actual directory is `AI_Slop_MDs/`

3. **§9 Directory Structure — missing top-level entries**
   - Doc omits: `infrastructure/` (has `systemd/`, `wifi-manager/`, `rtl-sdr-setup.sh`), `Makefile`, `README.md`, `SYSTEM_ARCHITECTURE.md`

4. **§3.3 + §6.1 — GPSService WebSocket host is not hardcoded `localhost`**
   - Doc: "connects to gpsd-ws-bridge at `ws://localhost:8765`"
   - Actual `config.ts`: host = `window.location.hostname` (so remote devices on the same network auto-connect)

5. **§3.3 — Normalized bridge output fields description is wrong**
   - Doc lists GPSD *input* fields: `(lat, lon, altHAE, speed, track)`
   - Actual `normalizeGpsdTpv()` output: `{ lat, lon, latitude, longitude, altitude, speed, heading, bearing, timestamp, source }`
   - Bridge renames `track` → `heading`/`bearing`; `altHAE`/`alt` → `altitude`; adds aliases and `source`

6. **§6.1 — Codebase calls the WS connection "gpsfake", not "WebSocket mode"**
   - Frontend uses `connectToGPSFake()`, `GPS_CONFIG.GPSFAKE` everywhere
   - Doc calls it "WebSocket mode (production): connects to gpsd-ws-bridge"
   - Terminology mismatch makes doc hard to cross-reference with code

---

## Clarity Issues

7. **§4.2 + §8.1 — Nothing documented calls `/ws/update-position`**
   - Endpoint described as "Receives GPS data from the bridge; updates TrackClient state"
   - HomeMapPage uses `gpsService` connecting directly to port 8765 — not this endpoint
   - Data flow §8.1 shows bridge → frontend directly, no bridge → FastAPI leg
   - TrackClient's in-memory state feeds `get_latest_track_point` and `is_new_road` — if nothing calls update-position, those always return (0.0, 0.0)
   - Doc should clarify what calls this endpoint or note it as in-progress

8. **§1 diagram + §6.1 + §7.1 — nginx port confusion**
   - nginx inside container listens on port **80**; Docker maps to host port **3000** (`3000:80`)
   - Doc says "nginx :3000" and "served by nginx on port 3000" — correct from host perspective but misleading
   - §7.1 table should note "internal 80 → host 3000"

9. **§5.3 — `gps.import_track()` description overstates the function**
   - Doc: "Batch-imports an external track with same start/end time"
   - Actual SQL: just inserts one track row with `(NOW(), NOW())` — no points imported
   - Better description: "Creates a pre-completed track stub for external data import"

10. **§8.2 data flow — trigger vs function name**
    - Flow diagram labels step as `gps.update_track_line_trigger()` (the function)
    - Actual trigger is named `trg_update_track_line`, which calls `gps.update_track_line_trigger()`
