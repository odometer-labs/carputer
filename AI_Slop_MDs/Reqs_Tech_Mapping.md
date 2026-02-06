# Requirements to Tech Stack Mapping

This document maps each project requirement to the specific technologies and implementations across the four team tech stacks.

---

## ✅ Requirement 1: Track Drives & Alert on New Roads

**"Tracks my drives as GPS tracks and alerts me when I'm on a new road"**

### Implementation:

**Embedded Team:**
- **gpsd** - Collects GPS position data from USB/UART GPS module
- **Python service** - Reads from gpsd, streams to backend

**Backend Team:**
- **PostgreSQL + PostGIS** - Stores track points with spatial geometry
- **Smart Beaconing Algorithm** - Adaptive point storage based on speed/heading changes
- **New Road Detection Logic**:
  ```python
  # Spatial query to find nearby historical tracks
  SELECT COUNT(*) FROM road_segments 
  WHERE ST_DWithin(geometry, ST_MakePoint(current_lon, current_lat), 100)
  ```
  - If no tracks within threshold → **NEW ROAD ALERT**
- **WebSocket API** - Streams new road events to frontend

**Frontend Team:**
- **Svelte store** - Receives real-time GPS updates
- **Toast notification** (svelte-sonner) - Displays "New Road Detected!" alert
- **MapLibre GL JS** - Shows current position on map

**Status:** ✅ Fully covered

---

## ✅ Requirement 2: Automatic Launch at Boot

**"Automatic launch of app at boot time"**

### Implementation:

**Infrastructure Team:**
- **systemd services** for all components:
  ```ini
  # /etc/systemd/system/carputer-backend.service
  [Unit]
  After=network.target postgresql.service
  
  [Service]
  ExecStart=/opt/carputer/venv/bin/python backend.py
  Restart=always
  
  [Install]
  WantedBy=multi-user.target
  ```

**Embedded Team:**
- **systemd service** for gpsd (auto-starts GPS daemon)
- **systemd service** for direwolf (APRS receiver)

**Frontend Team:**
- **Chromium kiosk mode** OR **systemd service** to launch web UI:
  ```ini
  [Service]
  ExecStart=/usr/bin/chromium-browser --kiosk http://localhost:8000
  ```

**Infrastructure Team:**
- **Boot optimization** - Disabled unnecessary services for faster boot

**Status:** ✅ Fully covered

---

## ✅ Requirement 3: Touch-Based Interface

**"A touch-based interface"**

### Implementation:

**Frontend Team:**
- **Svelte** - Reactive framework perfect for touch
- **shadcn-svelte** - Touch-friendly component library
- **Tailwind CSS** - Touch target sizing:
  ```css
  .touch-target { @apply min-h-12 min-w-12 p-3; }
  .btn-touch { @apply h-14 px-6 text-lg; }
  ```
- **Custom Svelte actions** for gestures:
  - Swipe left/right (navigate tracks)
  - Long press (context menus)
  - Pinch/zoom on map
- **Large fonts** for readability while driving

**Embedded Team:**
- **Touch display drivers** - Configured for Raspberry Pi Touch Display
- **Calibration** - Touch input calibration on first boot

**Status:** ✅ Fully covered

---

## ✅ Requirement 4: PostgreSQL Database for Geographic Data

**"A postgresql database storing all of the geographic information"**

### Implementation:

**Backend Team:**
- **PostgreSQL 15+** - Primary database
- **PostGIS 3.3+** - Spatial extension for geographic data
- **Tables**:
  - `tracks` - Track metadata
  - `track_points` - GPS coordinates with GEOMETRY(Point, 4326)
  - `road_segments` - Historical road data with GEOMETRY(LineString, 4326)
  - `aprs_stations` - APRS station positions
  - `aprs_history` - APRS position time-series
- **Spatial indexes** (GiST) - Fast proximity queries
- **SQLAlchemy + GeoAlchemy2** - ORM with PostGIS integration

**Infrastructure Team:**
- **PostgreSQL configuration** - Tuned for Raspberry Pi
- **Database backups** - Automated pg_dump to USB/network

**Status:** ✅ Fully covered

---

## ✅ Requirement 5: RTL-SDR APRS Integration

**"Integration with an RTL-SDR or other radio system to receive surrounding APRS broadcasts"**

### Implementation:

**Embedded Team:**
- **RTL-SDR drivers** (rtl-sdr package) - USB dongle support
- **Direwolf 1.7+** - Software TNC for APRS decoding
- **rtl_fm** - FM demodulation from RTL-SDR
- **PulseAudio/pipewire** - Audio routing: RTL-SDR → Direwolf
- **aprslib** (Python) - Parse APRS packets into structured data
- **No license required** - Reception only (no transmission)

**Backend Team:**
- **APRS data pipeline**:
  1. Direwolf outputs decoded packets
  2. Python service reads via KISS interface
  3. Parse with aprslib
  4. Store in PostgreSQL (aprs_stations, aprs_history tables)
- **Database schema**:
  ```sql
  CREATE TABLE aprs_stations (
      callsign VARCHAR(9) PRIMARY KEY,
      geom GEOMETRY(Point, 4326),
      last_seen TIMESTAMP,
      symbol VARCHAR(2),
      comment TEXT
  );
  ```

**Frontend Team:**
- **APRS markers** on map (MapLibre GL JS)
- **Layer toggle** - Show/hide APRS stations
- **Click for details** - Callsign, last seen, comment

**Status:** ✅ Fully covered

---

## ✅ Requirement 6: Map Display with GPS Track Overlays

**"A display overlaying GPS tracks on something like openstreetmaps data"**

### Implementation:

**Frontend Team:**
- **MapLibre GL JS** - Vector/raster map rendering
- **Track layer rendering**:
  ```typescript
  map.addLayer({
    id: 'tracks-layer',
    type: 'line',
    source: 'tracks',
    paint: {
      'line-color': ['get', 'color'],
      'line-width': 3
    }
  });
  ```
- **Current position marker** - Real-time GPS location
- **Nearby tracks query** - Show tracks within configurable distance
- **Layer controls** - Toggle individual tracks on/off
- **Performance optimization**:
  - Track simplification (@turf/simplify)
  - Virtual scrolling for track list
  - Debounced map updates

**Backend Team:**
- **Spatial query for nearby tracks**:
  ```sql
  SELECT t.id, t.name, ST_AsGeoJSON(tp.geom) as geojson
  FROM tracks t
  JOIN track_points tp ON t.id = tp.track_id
  WHERE ST_DWithin(tp.geom, ST_MakePoint($lon, $lat), 0.01)
  ```
- **REST API endpoint**: `GET /api/tracks/nearby?lat=45.5&lon=-122.6&radius=1000`

**Infrastructure Team:**
- **Map tile server** - Serves OpenStreetMap tiles (online/offline)

**Status:** ✅ Fully covered

---

## ✅ Requirement 7: Smart Beaconing for Track Storage

**"Constant storage of GPS track data, using something like the APRS smart beaconing algorithm"**

### Implementation:

**Backend Team:**
- **Smart Beaconing Algorithm** implementation:
  ```python
  def should_beacon(current_pos, last_beacon):
      # Beacon on significant speed change
      if abs(current_pos.speed - last_beacon.speed) > SPEED_THRESHOLD:
          return True
      
      # Beacon on heading change (corner detection)
      if abs(current_pos.heading - last_beacon.heading) > HEADING_THRESHOLD:
          return True
      
      # Beacon after minimum time interval
      if (current_pos.timestamp - last_beacon.timestamp) > MIN_INTERVAL:
          return True
      
      # Beacon after minimum distance
      if distance(current_pos, last_beacon) > MIN_DISTANCE:
          return True
      
      return False
  ```
- **Libraries**: geopy (distance calculations), pyproj (coordinate transforms)
- **Database insertion** - Only store points when beacon condition met

**Embedded Team:**
- **Continuous GPS data** - gpsd provides position updates every second
- **Python service** - Applies smart beaconing logic before sending to backend

**Status:** ✅ Fully covered

---

## ✅ Requirement 8: Web-Based Interface for Management

**"A web-based interface to view GPS tracks and manage the system"**

### 8a. Import/Export GPS Tracks

**Frontend Team:**
- **File upload component**:
  ```svelte
  <input type="file" accept=".gpx,.kml,.geojson" 
         on:change={handleUpload} />
  ```
- **Drag-and-drop support**
- **Export buttons** - Download as GPX, KML, GeoJSON, CSV

**Backend Team:**
- **Import API endpoints**:
  - `POST /api/import/gpx` - Parse GPX with gpxpy
  - `POST /api/import/kml` - Parse KML with fastkml
  - `POST /api/import/geojson` - Parse GeoJSON
- **Export API endpoints**:
  - `GET /api/export/{track_id}/gpx`
  - `GET /api/export/{track_id}/geojson`
- **Libraries**: gpxpy, fastkml, geojson, pandas

### 8b. System Updates

**Infrastructure Team:**
- **Web interface for updates**:
  - Check for updates button
  - Display current version / available version
  - Trigger update process
- **Update mechanisms**:
  - `unattended-upgrades` for security patches
  - Git pull for application updates
  - SvelteKit build and restart

**Frontend Team:**
- **Settings page** with system management
- **Update status display**
- **Confirmation dialogs**

### 8c. System Health Dashboard

**Frontend Team:**
- **Dashboard page** with widgets:
  - CPU temperature gauge
  - Disk space usage (chart)
  - Memory usage (chart)
  - GPS fix status (satellite count, HDOP)
  - Database statistics (# tracks, # points, size)
  - Uptime counter
  - Current patch level
  - APRS reception rate

**Backend Team:**
- **Health API endpoint**: `GET /api/system/health`
  ```json
  {
    "cpu_temp": 52.3,
    "disk_usage": 45.2,
    "memory_usage": 60.1,
    "gps_status": {
      "fix": true,
      "satellites": 12,
      "hdop": 1.2
    },
    "track_count": 142,
    "total_points": 523847,
    "db_size_mb": 2341,
    "uptime_hours": 168,
    "patch_level": "2025.02.05"
  }
  ```

**Infrastructure Team:**
- **Monitoring scripts** - Collect system metrics
- **systemd integration** - Service health checks

**Status:** ✅ Fully covered

---

## ✅ Requirement 9: Headless Operation

**"The ability to run headless, with all functionality accessible via the web interface"**

### Implementation:

**Infrastructure Team:**
- **No GUI required** - Can run with Raspberry Pi OS Lite
- **SSH access** - For remote administration
- **mDNS (Avahi)** - Access via `raspberrypi.local`

**Frontend Team:**
- **Responsive web interface** - Accessible from any device on network:
  - Laptop
  - Phone
  - Tablet
- **SvelteKit** - Full-featured web app, no native app needed

**Backend Team:**
- **All features via REST API** - No local interaction required
- **WebSocket** - Real-time updates work over network

**Embedded Team:**
- **Services run as daemons** - No display needed:
  - gpsd
  - direwolf
  - Backend API
  - Frontend server

**Status:** ✅ Fully covered

---

## ✅ Requirement 10: Online/Offline Map Functionality

**"Online and offline map functionality, with the ability to download map data for offline use"**

### Implementation:

**Infrastructure Team:**

**Option 1: Vector Tiles (Recommended)**
- **Tileserver-GL** - Serves Mapbox Vector Tiles
- **OpenMapTiles** - Pre-generated vector tiles
- **Storage**: 10-15GB for US, 2-5GB for region
- **Download process**:
  ```bash
  # One-time download of region
  wget https://data.maptiler.com/downloads/tileset/osm/north-america.mbtiles
  ```

**Option 2: Raster Tiles**
- **nginx + mod_tile** - Serve pre-rendered PNG tiles
- **Pre-render tiles** with tilestache-seed
- **Storage**: Larger than vector tiles

**Option 3: MBTiles + mbtileserver (Simplest)**
- **Download MBTiles** file for region
- **mbtileserver** - Lightweight Go server
- **No rendering** - Pre-rendered tiles in single file

**Frontend Team:**
- **MapLibre GL JS** - Supports both online and offline tiles
- **Tile source configuration**:
  ```typescript
  // Online
  style: 'https://api.maptiler.com/maps/...'
  
  // Offline
  style: 'http://localhost:8080/styles/basic/style.json'
  ```
- **PWA service worker** - Cache tiles for offline use

**Backend Team:**
- **Map download API** (optional):
  - `POST /api/maps/download` - Initiate download for region
  - `GET /api/maps/status` - Download progress

**Status:** ✅ Fully covered

---

## ✅ Requirement 11: Automatic WiFi Hotspot

**"Automatic wifi hotspot functionality, with the ability to connect to known networks and create a hotspot when no known networks are available"**

### Implementation:

**Infrastructure Team:**
- **NetworkManager** - Handles all network logic
- **Automatic switching**:
  1. On boot, scan for known networks
  2. If found → Connect to strongest
  3. If not found → Enable hotspot mode
- **Configuration**:
  ```bash
  # Create hotspot profile
  nmcli device wifi hotspot ssid "Carputer-Hotspot" password "yourpassword"
  
  # Set priority for known networks
  nmcli connection modify "Home-WiFi" connection.autoconnect-priority 100
  nmcli connection modify "Carputer-Hotspot" connection.autoconnect-priority 10
  ```
- **Python monitoring service**:
  ```python
  # Monitor network state
  if not connected_to_known_network():
      enable_hotspot()
  ```
- **DHCP server** (dnsmasq) - Provides IPs to connected devices
- **mDNS (Avahi)** - Makes `carputer.local` discoverable

**Frontend Team:**
- **Network settings page**:
  - List known WiFi networks
  - Add new network
  - View hotspot settings (SSID, password)
  - See connected devices

**Backend Team:**
- **Network management API**:
  - `GET /api/network/status` - Current connection
  - `POST /api/network/add` - Add known network
  - `GET /api/network/devices` - Connected devices to hotspot

**Status:** ✅ Fully covered

---

## Summary: All Requirements Met ✅

| # | Requirement | Embedded | Backend | Frontend | Infrastructure |
|---|-------------|----------|---------|----------|----------------|
| 1 | GPS tracking + new road alerts | ✅ | ✅ | ✅ | |
| 2 | Auto-launch at boot | ✅ | | ✅ | ✅ |
| 3 | Touch interface | ✅ | | ✅ | |
| 4 | PostgreSQL database | | ✅ | | ✅ |
| 5 | RTL-SDR APRS reception | ✅ | ✅ | ✅ | |
| 6 | Map with track overlays | | ✅ | ✅ | ✅ |
| 7 | Smart beaconing storage | ✅ | ✅ | | |
| 8a | Import/export tracks | | ✅ | ✅ | |
| 8b | System updates | | ✅ | ✅ | ✅ |
| 8c | Health dashboard | | ✅ | ✅ | ✅ |
| 9 | Headless operation | ✅ | ✅ | ✅ | ✅ |
| 10 | Online/offline maps | | | ✅ | ✅ |
| 11 | Auto WiFi hotspot | | ✅ | ✅ | ✅ |

---

## Tech Stack Summary

**Embedded:**
- gpsd, RTL-SDR, Direwolf, aprslib, systemd

**Backend:**
- FastAPI, PostgreSQL + PostGIS, SQLAlchemy, geopy, gpxpy, fastkml

**Frontend:**
- Svelte + SvelteKit, MapLibre GL JS, shadcn-svelte, Tailwind CSS

**Infrastructure:**
- NetworkManager, Tileserver-GL, Ansible/pi-gen, nginx, systemd

All requirements are fully addressed by the recommended tech stacks!
