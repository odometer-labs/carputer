# Carputer System Architecture

**Project:** Odometer Labs GPS Carputer
**Repo:** `odometer-labs/carputer`

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Hardware Layer](#2-hardware-layer)
3. [Embedded / On-Device Layer](#3-embedded--on-device-layer)
4. [API Layer](#4-api-layer)
5. [Database Layer](#5-database-layer)
6. [Frontend Layer](#6-frontend-layer)
7. [Infrastructure & DevOps](#7-infrastructure--devops)
8. [Data Flow Diagrams](#8-data-flow-diagrams)
9. [Directory Structure](#9-directory-structure)
10. [Technology Stack Summary](#10-technology-stack-summary)

---

## 1. System Overview

Carputer is an in-vehicle navigation and GPS tracking computer that runs entirely on local hardware. It records drive tracks, displays a real-time map, and detects when the driver travels a previously unvisited road ("road discovery"). The system is designed to operate without a persistent internet connection once map tiles are downloaded.

**Planned addition:** An RTL-SDR USB dongle will receive APRS (Automatic Packet Reporting System) transmissions on 144.390 MHz. A Direwolf software TNC will decode packets, and a Python bridge will ingest them into PostgreSQL for display on the map.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           In-Vehicle Hardware                            │
│                                                                          │
│  ┌────────────────┐  serial   ┌──────────┐  SHM   ┌──────────┐         │
│  │ u-blox ZED-F9P │──────────►│  GPSD    │───────►│  Chrony  │         │
│  │  GNSS Module   │ /dev/     │  :2947   │        │  (time)  │         │
│  └────────────────┘ ttyACM0   └────┬─────┘        └──────────┘         │
│                                    │ TCP                                 │
│                               ┌────▼──────────┐                         │
│                               │ gpsd-ws-bridge│                         │
│                               │   (Node.js)   │                         │
│                               │    :8765      │                         │
│                               └────┬──────────┘                         │
│                                    │ WebSocket                           │
│  ┌─────────────────────────────────▼─────────────────────────────────┐  │
│  │                    Docker Network: carputer                       │  │
│  │                                                                   │  │
│  │  ┌──────────────┐   REST/WS   ┌─────────────────────────────┐    │  │
│  │  │  Frontend    │◄───────────►│  FastAPI (api)              │    │  │
│  │  │  Svelte+Vite │  /v1/ /ws   │  :8000                      │    │  │
│  │  │  nginx :3000 │             └────────────┬────────────────┘    │  │
│  │  └──────────────┘                          │ psycopg             │  │
│  │                                  ┌─────────▼──────────────────┐  │  │
│  │                                  │  PostgreSQL 17 + PostGIS   │  │  │
│  │                                  │  :5432                     │  │  │
│  │                                  └────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────┐  (deployed by infrastructure/script.sh)           │
│  │  RTL-SDR Dongle  │──USB──► rtl_fm → Direwolf (KISS :8001)           │
│  │  144.390 MHz     │         → Python APRS bridge → FastAPI ingest     │
│  └──────────────────┘                                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Hardware Layer

### Primary Compute: Raspberry Pi 4 Model B (1GB)

| Property | Value |
|---|---|
| SoC | Broadcom BCM2711 |
| CPU | Quad-core ARM Cortex-A72 (ARMv8) 64-bit @ 1.8 GHz |
| RAM | 1 GB LPDDR4-3200 SDRAM |
| Storage | Micro-SD card slot |
| Video Out | 2× micro-HDMI (up to 4Kp60) |
| USB | 2× USB 3.0, 2× USB 2.0 |
| Networking | Gigabit Ethernet, 802.11ac (2.4/5 GHz) WiFi, Bluetooth 5.0/BLE |
| GPIO | 40-pin header (backwards compatible) |
| Power | 5V DC via USB-C (min. 3A) or 5V via GPIO header |
| Operating Temp | 0–50°C ambient |

### GNSS Receiver: u-blox C099-F9P Application Board

| Property | Value |
|---|---|
| Module | u-blox ZED-F9P (high-precision RTK GNSS) |
| Protocol | NMEA over serial + optional PPS pulse |
| Interface | USB (appears as `/dev/ttyACM0`) |
| Power | DC barrel jack, 6V–12V |
| Accuracy | Sub-meter (RTK), ~1m standalone |

### GNSS Antenna

External active patch antenna with ground plane, connected to the C099-F9P board.

### RTL-SDR USB Dongle

| Property | Value |
|---|---|
| Purpose | Receive APRS packets on 144.390 MHz (2m amateur band) |
| Interface | USB (appears as `/dev/bus/usb/...`; requires `rtl-sdr` kernel driver) |
| Driver blacklist | `/etc/modprobe.d/blacklist-rtl.conf` must blacklist `dvb_usb_rtl28xxu` |
| Software | `rtl_fm` (FM demodulation) → `Direwolf` (AX.25 / APRS decoder) |
| Direwolf KISS port | TCP 8001 |

---

## 3. Embedded / On-Device Layer

All embedded services are managed by **systemd** and must start in a strict order:

```
chrony.service → gpsd.service → carputer.service
```

APRS services are deployed by `infrastructure/script.sh` and start independently after the network is available:

```
network.target → aprs-receiver.service → aprs-bridge.service
```

### 3.1 GPSD

- Reads raw NMEA sentences and PPS signal from the GPS module over `/dev/ttyACM0`
- Listens for client connections on **TCP port 2947**
- Writes time data into shared memory (SHM) segments for chrony:
  - `SHM 0` — NMEA sentence time (~100 ms accuracy)
  - `SHM 1` — PPS pulse time (~1 µs accuracy, requires TIME_PULSE pin)

### 3.2 Chrony (NTP/GPS Time Sync)

- Configured at `embedded/ntp_gps_sync/chrony.conf`
- Reads SHM 0 (NMEA) and SHM 1 (PPS) from GPSD to discipline the system clock
- Falls back to public NTP pool servers when no GPS fix is available
- A systemd drop-in (`gpsd-depends-chrony.conf`) enforces that GPSD starts only after chrony is ready

### 3.3 gpsd-ws-bridge (`frontend/carputer-web-app/scripts/gpsd-ws-bridge.mjs`)

A lightweight **Node.js** bridge process that:
1. Connects to GPSD over TCP (`localhost:2947`)
2. Sends the `?WATCH={"enable":true,"json":true}` command to subscribe to GPS updates
3. Filters GPSD packets to only process **TPV** (Time-Position-Velocity) reports
4. Normalizes the TPV report into a consistent JSON object: `{ lat, lon, latitude, longitude, altitude, speed, heading, bearing, timestamp, source }`
5. Broadcasts normalized position data to all connected WebSocket clients on **port 8765**
6. Auto-reconnects to GPSD with a 1-second backoff on disconnect

**Environment variables:**

| Variable | Default | Description |
|---|---|---|
| `GPSD_HOST` | `127.0.0.1` | GPSD TCP host |
| `GPSD_PORT` | `2947` | GPSD TCP port |
| `WS_HOST` | `0.0.0.0` | WebSocket bind host |
| `WS_PORT` | `8765` | WebSocket listen port |

### 3.4 APRS Reception Pipeline

The APRS pipeline is fully implemented in `infrastructure/script.sh`. Running the script on the Pi generates the config and scripts and installs the systemd services. Files are deployed to `/opt/carputer/aprs/` — they are not checked into the repo.

**`aprs-receiver.service`** — runs `rtl_fm` piped into `Direwolf`:

```
rtl_fm -f 144390000 -s 24000 -g 49.6 -p 0 -d 0 - | direwolf -c /opt/carputer/aprs/direwolf.conf -r 24000 -D 1 -
```

- `rtl_fm` tunes the RTL-SDR to 144.390 MHz and demodulates FM audio at 24 kHz
- `Direwolf` decodes 1200-baud AFSK AX.25 and serves a KISS TCP socket on **port 8001**
- Config file: `/opt/carputer/aprs/direwolf.conf` (generated at deploy time)

**`aprs-bridge.service`** — Python script (`/opt/carputer/aprs/aprs_bridge.py`, generated at deploy time):

1. Connects to Direwolf KISS TCP socket (`localhost:8001`)
2. Parses raw AX.25 frames into APRS packets
3. Extracts position reports (callsign, lat, lon, symbol, comment)
4. POSTs each packet to `POST /v1/aprs/ingest` on the FastAPI backend
5. Logs to `/var/log/carputer/aprs-bridge.log`

---

## 4. API Layer

**Location:** `api/`
**Framework:** FastAPI 0.129 (Python 3.13)
**Runtime:** Uvicorn (ASGI)
**Port:** 8000
**Docs:** `http://localhost:8000/docs` (Swagger UI)

### 4.1 REST Endpoints (`/v1/`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/tracks` | List all completed and active tracks (GeoJSON LineStrings) |
| `GET` | `/v1/tracks/{track_id}` | Get a single track by ID (GeoJSON LineString) |
| `PUT` | `/v1/tracks/{track_id}` | Update a track's start/end timestamps |
| `DELETE` | `/v1/tracks/{track_id}` | Delete a track and all its points (cascading) |
| `POST` | `/v1/tracks-start` | Start a new recording session (or return the active one) |
| `GET` | `/v1/tracks-end` | End the active recording session |
| `POST` | `/v1/tracks/point/{track_id}` | Add a GPS track point to a track |
| `GET` | `/v1/tracks-latest-point` | Get the most recent GPS telemetry point |
| `GET` | `/v1/tracks-check-new-road` | Check if the latest position is on a new road (>30m from any prior track) |

**Planned APRS endpoints (`/v1/aprs/`):**

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/aprs/ingest` | Receive a decoded APRS packet from the bridge; upsert station + insert packet history |
| `GET` | `/v1/aprs/stations` | List all known APRS stations (GeoJSON Points) |
| `GET` | `/v1/aprs/stations/{callsign}` | Get a single station's current position and recent packet history |

### 4.2 WebSocket Endpoints (`/ws/`)

| Path | Direction | Description |
|---|---|---|
| `/ws/get-position` | Server → Client | Streams current GPS state (lat, lon, speed, heading) at **4 Hz** (every 250 ms) |
| `/ws/update-position` | Client → Server | Receives GPS data and updates the in-memory `TrackClient` state; intended to keep the API's position current for road-discovery and latest-point queries |

### 4.3 Core Components

**`TrackClient`** (`api/app/clients/track_client.py`)
A singleton that:
- Holds the current in-memory GPS state: `latitude`, `longitude`, `speed`, `heading`
- Wraps all database calls using `psycopg` (PostgreSQL adapter)
- Acts as the single source of truth for current position, shared between the REST and WebSocket routers

**`dependencies.py`**
`get_connection()` — opens a new `psycopg` connection using env vars (`DB_HOST`, `DB_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`). Returns results as dicts via `dict_row` row factory.

**Models** (Pydantic)
- `Track` — `start_time: datetime`, `end_time: datetime`
- `TrackPoint` — `latitude: float`, `longitude: float`, `speed: float` (m/s), `heading: float` (0–360°)

### 4.4 Key Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` + `uvloop` | ASGI server |
| `psycopg` + `psycopg-binary` | PostgreSQL client |
| `pydantic` | Request/response validation |
| `python-dotenv` | `.env` config loading |
| `gpsdclient` | GPSD client library |
| `websockets` | WebSocket support |
| `sentry-sdk` | Error monitoring |

---

## 5. Database Layer

**Image:** `imresamu/postgis:17-3.5-bookworm` (PostgreSQL 17 + PostGIS 3.5)
**Port:** 5432
**Schema:** `gps`
**Init SQL:** `backend/geotracker/migrations/gps_functions.sql`
**Data Volume:** `postgres_data` (Docker named volume)

### 5.1 Tables

#### `gps.tracks`
```sql
track_id   BIGSERIAL PRIMARY KEY
start_time TIMESTAMPTZ NOT NULL
end_time   TIMESTAMPTZ          -- NULL = currently active track
```
- A **unique partial index** (`one_active_track`) ensures only one recording session is active at a time.

#### `gps.track_points`
```sql
point_id   BIGSERIAL PRIMARY KEY
track_id   BIGINT REFERENCES gps.tracks(track_id) ON DELETE CASCADE
time_stamp TIMESTAMPTZ NOT NULL
geom       GEOGRAPHY(Point, 4326)   -- WGS84
speed_mph  DOUBLE PRECISION
heading_deg DOUBLE PRECISION        -- 0–360°, 0 = North
```

#### `gps.track_lines`
```sql
track_id BIGINT PRIMARY KEY REFERENCES gps.tracks(track_id) ON DELETE CASCADE
geom     GEOGRAPHY(LINESTRING, 4326)
```
Automatically maintained by trigger (see §5.3).

#### `gps.aprs_stations` *(planned)*
```sql
callsign     VARCHAR(20) PRIMARY KEY
geom         GEOGRAPHY(Point, 4326)   -- most recent position
last_seen    TIMESTAMPTZ NOT NULL
symbol_table CHAR(1)                  -- APRS symbol table identifier
symbol_code  CHAR(1)                  -- APRS symbol code
comment      TEXT
```
One row per callsign; updated in-place on each new position report.

#### `gps.aprs_packets` *(planned)*
```sql
packet_id    BIGSERIAL PRIMARY KEY
callsign     VARCHAR(20) REFERENCES gps.aprs_stations(callsign)
geom         GEOGRAPHY(Point, 4326)   -- position at time of packet
received_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
raw_packet   TEXT
```
Append-only history of every received APRS frame.

### 5.2 Spatial Indexes

| Index | Type | Columns | Purpose |
|---|---|---|---|
| `idx_track_points_geom` | GIST | `track_points.geom` | Fast proximity searches |
| `idx_track_points_geom_track` | GIST | `(geom, track_id)` | Combined spatial+ID queries |
| `idx_track_points_track_time` | B-tree | `(track_id, time_stamp)` | Time-ordered point queries |
| `idx_track_points_timestamp` | B-tree | `time_stamp DESC` | Latest point lookup |
| `idx_track_lines_geom` | GIST | `track_lines.geom` | LineString proximity searches |
| `idx_aprs_stations_geom` *(planned)* | GIST | `aprs_stations.geom` | Station proximity queries |
| `idx_aprs_packets_callsign_time` *(planned)* | B-tree | `(callsign, received_at DESC)` | Per-station packet history |
| `idx_aprs_packets_geom` *(planned)* | GIST | `aprs_packets.geom` | Spatial queries over packet history |

### 5.3 Stored Functions & Procedures

| Name | Type | Description |
|---|---|---|
| `gps.create_track()` | FUNCTION → BIGINT | Starts a new track or returns the currently active one |
| `gps.add_track_point(...)` | PROCEDURE | Inserts a GPS point (lat, lon, speed, heading) into a track |
| `gps.end_track()` | PROCEDURE | Stamps `end_time = NOW()` on the active track |
| `gps.retrieve_track(id)` | FUNCTION → TABLE | Returns a single track as a GeoJSON LineString |
| `gps.view_all_tracks()` | FUNCTION → TABLE | Returns all tracks as GeoJSON LineStrings |
| `gps.update_track(id, ...)` | PROCEDURE | Manually corrects track timestamps |
| `gps.delete_track(id)` | PROCEDURE | Cascading delete of track + points + line |
| `gps.get_latest_track_point()` | FUNCTION → TABLE | Returns the most recent telemetry point |
| `gps.is_new_road()` | FUNCTION → BOOLEAN | Returns TRUE if latest point is >30m from all prior track lines |
| `gps.get_track_lines_near_location(meters)` | FUNCTION → TABLE | Historical tracks within N meters of current position |
| `gps.get_track_lines_using_road()` | FUNCTION → TABLE | Historical tracks that overlap (within 30m) the current active track |
| `gps.import_track()` | FUNCTION → INTEGER | Creates a pre-completed track stub (`start_time = NOW(), end_time = NOW()`) for external data import; caller must add points separately |
| `gps.validate_geometry(id)` | PROCEDURE | Fixes self-intersections in a track's LineString |
| `gps.upsert_aprs_station(...)` *(planned)* | PROCEDURE | Insert or update a station's position and metadata |
| `gps.get_aprs_stations_near(meters)` *(planned)* | FUNCTION → TABLE | APRS stations within N meters of current position |

### 5.4 Trigger: `trg_update_track_line`

Fires **AFTER INSERT** on `gps.track_points` for each row.
- If a LineString already exists for the track: appends the new point with `ST_AddPoint`
- If no LineString exists yet and there are ≥2 points: creates one with `ST_MakeLine`

This avoids recomputing the full LineString on every read.

### 5.5 Geotracker Library (`backend/geotracker/`)

A Python library stub (currently in development) intended to encapsulate spatial logic and database access for the backend service. Managed with `uv` (Python package manager). Runs as an optional Docker Compose profile (`--profile backend`).

---

## 6. Frontend Layer

### 6.1 In-Car Web App (`frontend/carputer-web-app/`)

The primary user interface, rendered on the in-vehicle display.

**Stack:** Svelte + TypeScript + Vite, served by **nginx** (listens on port 80 inside the container; exposed as port 3000 on the host via Docker).
**Routing:** `svelte-spa-router` (hash-based SPA routing)
**Testing:** Vitest + jsdom

#### Pages

| Page | Route | Description |
|---|---|---|
| `HomeMapPage` | `/` | Full-screen OpenLayers map with live GPS marker, APRS points, and track start/stop button |
| `DashboardPage` | `/Dashboard` | System info: track count, firmware version, import/export tracks |
| `WifiPage` | `/Wifi` | WiFi network management (toggle on/off, view connected/available networks) |
| `MapDownloadPage` | `/MapDownload` | Offline map tile download |
| `SettingPreferencePage` | `/SettingPreference` | User preferences (zoom level, icon size, day/night mode) |
| `ErrorPage` | `/Error` | Full-screen error display for fatal errors |

#### Key Services & Stores

**`GPSService`** (`src/fake-api/gpsService.ts`)
Abstracts the GPS data source with three modes:
1. **gpsfake mode** (default): connects to the `gpsd-ws-bridge` WebSocket server at `ws://<window.location.hostname>:8765`; parses the bridge's normalized JSON. The host resolves dynamically so remote devices on the same network connect automatically.
2. **NMEA playback** (dev/demo): replays recorded `.nmea` files (`kras-en.nmea`)
3. **Random mock** (fallback): generates small random position drift; also activates automatically if the gpsfake connection fails

**`trackStore`** (`src/stores/trackStore.ts`)
A Svelte writable store that wraps REST API calls:
- `trackStore.start()` → `POST /api/v1/tracks-start` → sets `isTracking: true`, stores `trackId`
- `trackStore.end()` → `GET /api/v1/tracks-end` → sets `isTracking: false`

**`preferences`** (`src/services/preferences.ts`)
Persists user preferences (default zoom, icon size, day/night mode) to `localStorage`.

**`errorStore`** (`src/stores/errorStore.ts`)
Manages two error tiers:
- **Vital errors** — route to `ErrorPage`
- **Non-vital errors** — show `ErrorPopup` overlay

#### UI Components

| Component | Description |
|---|---|
| `SystemIndicators` | Status bar showing WiFi, time, and road-discovery indicators |
| `WifiIndicator` | Animated WiFi signal-strength icon (4 levels) |
| `TimeIndicator` | Formatted current time |
| `RoadDiscoverIndicator` | Lights up when the current road is newly discovered |
| `DarkLightIndicator` | Day/night mode toggle indicator |
| `BackButton` | SPA navigation back button |
| `ErrorPopup` | Non-fatal error overlay |

#### Map Features (`HomeMapPage`)

- **OpenLayers** map with **OpenStreetMap** tile layer
- User position marker:
  - Directional arrow SVG (follows heading) when tracking is locked
  - Plain blue circle when follow-lock is released
- **Follow modes:** position-lock only vs. position + heading (compass mode — rotates map)
- **APRS points:** clustered icon overlay (currently renders 10 hardcoded placeholder points; live data pending the RTL-SDR pipeline and `gps.aprs_stations` table)
- One-finger drag breaks follow-lock; two-finger pinch preserves it

#### nginx Proxy (`nginx.conf`)

| Path | Proxy Target | Purpose |
|---|---|---|
| `/api/` | `http://api:8000/` | REST API calls |
| `/ws` | `http://api:8000/ws` | WebSocket upgrade (GPS position streaming) |
| `/*` | `index.html` | SPA fallback |

### 6.2 Remote Web Interface (`frontend/carputer-remote-web-interface/`)

A separate Svelte + TypeScript application for remote management (e.g., from a laptop on the same network).

**Pages:** `HomePage`, `TracksPage` (track viewer), `LogsPage`, `ManageDataPage`

---

## 7. Infrastructure & DevOps

### 7.1 Docker Compose

#### Development (`docker-compose.yml`)
Builds all images locally from source.

| Service | Image | Port | Notes |
|---|---|---|---|
| `api` | Built from `./api` | 8000 | Waits for DB health check |
| `frontend` | Built from `./frontend/carputer-web-app` | 3000→80 | nginx (internal 80, host 3000); waits for `api` |
| `db` | `imresamu/postgis:17-3.5-bookworm` | 5432 | Init SQL auto-applied |
| `adminer` | `adminer` | 8080 | DB admin UI |
| `geotracker` | Built from `./backend` | — | Optional; enable with `--profile backend` |

#### Production (`docker-compose.prod.yml`)
Pulls pre-built multi-arch images from GitHub Container Registry for fast deployment to the Raspberry Pi 4.

| Image | Registry |
|---|---|
| API | `ghcr.io/odometer-labs/carputer-api:${VERSION}` |
| Frontend | `ghcr.io/odometer-labs/carputer-frontend:${VERSION}` |

All services share a single **bridge network** (`carputer`). The database uses a named volume (`postgres_data`) for persistence.

### 7.2 CI/CD (GitHub Actions)

#### `ci.yml` — Runs on push/PR to `main`, `development`, `dev/**`

| Job | Toolchain | Steps |
|---|---|---|
| `api-tests` | Python 3.13, pip | Install deps → `pytest` |
| `frontend-checks` | Node 22, npm | Install deps → `npm run lint` (eslint) → `npm run type-check` (tsc) → `npm run test -- --run` (vitest) |

#### `docker-build.yml`
Builds and pushes multi-architecture Docker images to GHCR on release/tag.

### 7.3 Dev Container

`.devcontainer/devcontainer.json` provides a reproducible development environment for VS Code / GitHub Codespaces.

### 7.4 Environment Configuration

Copy `.env.example` → `.env` and set:

```
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
```

---

## 8. Data Flow Diagrams

### 8.1 Live GPS Telemetry Flow

```
GPS Antenna
    │
    ▼
u-blox ZED-F9P (serial NMEA + PPS)
    │ /dev/ttyACM0
    ▼
GPSD (TCP :2947)
    │ TCP, JSON protocol
    ▼
gpsd-ws-bridge.mjs
    │ WebSocket :8765
    ▼
Frontend GPSService (browser WebSocket client)
    │
    ▼
HomeMapPage — renders position marker on OpenLayers map
    │
    └──(if tracking active)──► trackStore adds point via REST API
                                       │
                                       ▼
                              POST /api/v1/tracks/point/{id}
                                       │
                                       ▼
                              FastAPI → gps.add_track_point()
                                       │
                                       ▼
                              PostgreSQL → trg_update_track_line
                                       │
                                       ▼
                              gps.track_lines updated (LineString)
```

### 8.2 Track Recording Flow

```
User taps "Start Track"
    │
    ▼
trackStore.start()
    │
    ▼
POST /api/v1/tracks-start
    │
    ▼
gps.create_track() → returns track_id
    │
    ▼ (GPS position updates loop)
POST /api/v1/tracks/point/{track_id}
    │  (lat, lon, speed, heading)
    ▼
gps.add_track_point() → inserts into gps.track_points
    │
    ▼ (trigger fires: trg_update_track_line → gps.update_track_line_trigger())
updates gps.track_lines

User taps "Stop Track"
    │
    ▼
trackStore.end()
    │
    ▼
GET /api/v1/tracks-end
    │
    ▼
gps.end_track() → sets end_time = NOW()
```

### 8.3 Road Discovery Flow

```
(Periodic check)
GET /api/v1/tracks-check-new-road
    │
    ▼
gps.is_new_road()
    │ gets latest point via gps.get_latest_track_point()
    │ queries ST_Distance from latest point to all other track_lines
    │ within 500m using ST_DWithin
    ▼
Returns TRUE if nearest prior track line is > 30m away
    │
    ▼
RoadDiscoverIndicator lights up in SystemIndicators
```

### 8.4 APRS Reception Flow

Pipeline deployed by `infrastructure/script.sh`; FastAPI ingest endpoint and DB tables not yet implemented.

```
RF signal on 144.390 MHz (APRS)
    │
    ▼
RTL-SDR USB Dongle
    │ USB, raw IQ samples
    ▼
rtl_fm -f 144390000 -s 24000
    │ raw PCM audio piped via stdout
    ▼
Direwolf (software TNC)
    │ decodes 1200-baud AFSK AX.25
    │ KISS TCP :8001
    ▼
aprs_bridge.py (/opt/carputer/aprs/)
    │ parses AX.25 → APRS position reports
    │ HTTP POST /v1/aprs/ingest
    ▼
FastAPI — POST /v1/aprs/ingest
    │ validates packet, extracts callsign/lat/lon/symbol/comment
    ▼
gps.upsert_aprs_station()       gps.aprs_packets INSERT
    │ updates gps.aprs_stations       │ appends raw packet + geom
    ▼                                 ▼
/ws/get-aprs-stations (planned) — broadcasts new/updated station to frontend
    │
    ▼
HomeMapPage — renders APRS station markers on OpenLayers map
```

---

## 9. Directory Structure

```
carputer/
├── .devcontainer/          # VS Code dev container config
├── .github/
│   └── workflows/
│       ├── ci.yml          # Test + lint CI pipeline
│       └── docker-build.yml# Multi-arch Docker image builds
├── AI_Slop_MDs/            # Planning docs & architecture notes
├── api/                    # FastAPI service
│   ├── app/
│   │   ├── clients/
│   │   │   └── track_client.py   # Singleton GPS state + DB wrapper
│   │   ├── models/
│   │   │   ├── track.py          # Track Pydantic model
│   │   │   └── track_point.py    # TrackPoint Pydantic model
│   │   ├── routers/
│   │   │   ├── tracks.py         # REST /v1/ endpoints
│   │   │   └── websocket.py      # WS /ws/ endpoints
│   │   ├── logging/
│   │   ├── dependencies.py       # DB connection factory
│   │   └── main.py               # FastAPI app entry point
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── assets/
│   ├── datasheets/
│   │   └── hardware/       # Hardware docs & photos
│   ├── logos/
│   └── meeting_notes/
├── backend/                # Geotracker Python library (stub)
│   ├── geotracker/
│   │   ├── migrations/
│   │   │   └── gps_functions.sql # DB schema + all stored functions
│   │   └── src/
│   └── Dockerfile
├── embedded/               # On-device embedded config
│   ├── ntp_gps_sync/
│   │   ├── chrony.conf           # GPS-disciplined NTP config
│   │   └── gpsd-depends-chrony.conf # systemd drop-in
│   └── tests/              # Config validation tests
│
│   # Note: APRS files (direwolf.conf, aprs_bridge.py, start_aprs.sh) are
│   # generated at deploy time by infrastructure/script.sh and written to
│   # /opt/carputer/aprs/ on the Pi — they are not checked into the repo.
│
├── frontend/
│   ├── carputer-web-app/   # In-car Svelte app (primary UI)
│   │   ├── scripts/
│   │   │   └── gpsd-ws-bridge.mjs # GPSD → WebSocket bridge
│   │   ├── src/
│   │   │   ├── api/              # REST API client
│   │   │   ├── fake-api/         # GPSService + NMEA mock data
│   │   │   ├── pages/            # Page components
│   │   │   ├── assets/components/# Shared UI components
│   │   │   ├── stores/           # Svelte stores (track, error)
│   │   │   ├── services/         # preferences, etc.
│   │   │   └── utils/            # constants, navigation, time
│   │   ├── nginx.conf            # Production nginx config (internal port 80)
│   │   └── Dockerfile
│   └── carputer-remote-web-interface/  # Remote management UI
│       └── src/
│           └── pages/            # HomePage, TracksPage, LogsPage, ManageDataPage
├── infrastructure/         # Pi provisioning & system config
│   ├── systemd/
│   │   └── carputer.service      # Docker Compose auto-start service
│   ├── wifi-manager/       # WiFi management tooling
│   └── script.sh           # Full Pi setup script (installs all services)
├── docker-compose.yml      # Dev compose (build from source)
├── docker-compose.prod.yml # Prod compose (pull from GHCR)
├── Makefile
├── README.md
├── SYSTEM_ARCHITECTURE.md
└── .env.example
```

---

## 10. Technology Stack Summary

| Layer | Technology | Version |
|---|---|---|
| SBC | Raspberry Pi 4 Model B (BCM2711) | — |
| GNSS | u-blox ZED-F9P | — |
| SDR *(planned)* | RTL-SDR USB dongle | — |
| APRS Decoder *(planned)* | Direwolf | system |
| APRS FM Demod *(planned)* | rtl_fm (rtl-sdr tools) | system |
| GPS Daemon | GPSD | system |
| Time Sync | Chrony | system |
| WS Bridge | Node.js | 22 |
| API Framework | FastAPI | 0.129 |
| API Runtime | Uvicorn + uvloop | latest |
| API Language | Python | 3.13 |
| DB Client | psycopg | 3 |
| Database | PostgreSQL | 17 |
| Spatial Extension | PostGIS | 3.5 |
| Frontend Framework | Svelte | 5 |
| Frontend Language | TypeScript | 5 |
| Frontend Build | Vite | latest |
| Frontend Testing | Vitest | latest |
| Map Library | OpenLayers | latest |
| Map Tiles | OpenStreetMap | — |
| Web Server | nginx | alpine |
| Containerization | Docker + Compose | v2 |
| Image Registry | GitHub Container Registry | — |
| CI | GitHub Actions | — |
| Python Packaging | uv | latest |
