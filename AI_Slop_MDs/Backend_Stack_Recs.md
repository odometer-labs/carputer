# Backend Team Tech Stack Recommendations

## Overview
This document outlines the recommended technology stack for the Backend Team responsible for data processing, API development, database architecture, and core tracking logic for the Raspberry Pi GPS Tracking Carputer project.

---

## Core Backend Framework

### Web Framework
- **FastAPI** (Recommended)
  - Modern, fast (high-performance) Python web framework
  - Automatic API documentation (OpenAPI/Swagger)
  - Built-in async support for real-time operations
  - Type hints and Pydantic for data validation
  - WebSocket support for real-time GPS streaming
  - Native support for dependency injection
  
**Alternative:**
- **Flask** with Flask-RESTful
  - Lighter weight, simpler learning curve
  - More mature ecosystem
  - Good for smaller teams
  - Requires additional libraries for async operations

### API Architecture
- **RESTful API** for CRUD operations
- **WebSocket** for real-time GPS position streaming
- **Server-Sent Events (SSE)** alternative for one-way real-time updates

---

## Database Stack

### Primary Database
- **PostgreSQL 15+** with **PostGIS 3.3+**
  - PostGIS provides spatial data types and functions
  - Spatial indexing (GiST/BRIN indexes)
  - Efficient geometric operations
  - Support for geographic coordinate systems

### Python Database Drivers
- **psycopg2** or **psycopg3** - PostgreSQL adapter
- **SQLAlchemy 2.0+** - ORM and query builder
  - GeoAlchemy2 extension for PostGIS integration
  - Migration support via Alembic
  - Connection pooling

### Database Schema Considerations

#### Core Tables
```
tracks/
├── track_points (id, track_id, lat, lon, elevation, timestamp, speed, heading)
├── tracks (id, name, start_time, end_time, distance, metadata)
├── road_segments (id, geometry, first_seen, last_seen, visit_count)
├── aprs_stations (callsign, lat, lon, timestamp, symbol, comment)
└── aprs_history (id, callsign, lat, lon, timestamp, raw_packet)
```

#### Spatial Indexes
- GiST index on track_points.geom for proximity queries
- GiST index on road_segments.geometry for road matching
- BRIN index on track_points.timestamp for time-based queries

---

## Data Processing Pipeline

### Real-Time GPS Processing
- **Python asyncio** for concurrent GPS data handling
- **Redis** (optional) - In-memory buffer for real-time position streaming
- **Message Queue** (optional) - RabbitMQ or Redis Pub/Sub for event distribution

### Smart Beaconing Algorithm
**Implementation Approach:**
```python
# Adaptive beaconing based on:
- Speed changes (threshold-based)
- Heading changes (corner detection)
- Time intervals (minimum/maximum beacon intervals)
- Distance traveled (minimum distance between points)
```

**Libraries:**
- **geopy** - Distance and bearing calculations
- **pyproj** - Coordinate system transformations
- Custom Python implementation of APRS smart beaconing logic

### New Road Detection

**Algorithm Components:**
1. **Road Segment Matching**
   - Query road_segments within buffer distance of current position
   - Use PostGIS ST_DWithin for efficient spatial queries
   - Match current track to existing road segments

2. **Novelty Detection**
   - If no matching road segment found → NEW ROAD
   - Track distance from nearest historical track
   - Configurable threshold distance (e.g., 50-100 meters)

**Recommended Libraries:**
- **Shapely** - Geometric operations in Python
- **PostGIS functions** - ST_Distance, ST_DWithin, ST_Buffer, ST_Intersects

---

## APRS Data Processing

### APRS Packet Handling
- **aprslib** (Python) - Parse APRS packets
- **geopy** - Maidenhead grid square conversions (if needed)
- **pytz** - Timezone handling for timestamps

### Data Flow
```
Direwolf (Embedded) → KISS Interface → Backend Service
                                      ↓
                              Parse with aprslib
                                      ↓
                              Validate & Enrich
                                      ↓
                              Store in PostgreSQL
                                      ↓
                              Stream to Frontend (WebSocket)
```

---

## Import/Export Functionality

### Supported Formats
- **GPX** (GPS Exchange Format) - Primary format
- **KML/KMZ** (Keyhole Markup Language) - Google Earth
- **GeoJSON** - Web-friendly format
- **CSV** - Simple lat/lon/timestamp format
- **NMEA** - Raw GPS sentences (optional)

### Libraries
- **gpxpy** - GPX parsing and generation
- **fastkml** - KML parsing and generation
- **geojson** - GeoJSON handling
- **pandas** - CSV processing with geographic data

### Processing Pipeline
```python
# Import Pipeline
Upload → Format Detection → Validation → Parsing → 
Database Insertion → Track Metadata Generation → Success Response

# Export Pipeline
Track Selection → Format Specification → Query Database → 
Generate Output File → Compression (optional) → Download
```

---

## REST API Endpoints

### Core API Structure

#### Track Management
```
POST   /api/tracks/                    # Create new track
GET    /api/tracks/                    # List all tracks
GET    /api/tracks/{id}                # Get specific track
PUT    /api/tracks/{id}                # Update track metadata
DELETE /api/tracks/{id}                # Delete track
GET    /api/tracks/{id}/points         # Get track points
GET    /api/tracks/nearby              # Get tracks near location
```

#### Real-Time GPS
```
GET    /api/gps/current                # Current GPS position
WS     /api/gps/stream                 # WebSocket for real-time updates
GET    /api/gps/status                 # GPS lock status, satellite count
```

#### APRS
```
GET    /api/aprs/stations              # Active APRS stations
GET    /api/aprs/history/{callsign}    # Station position history
GET    /api/aprs/nearby                # Stations near current position
```

#### Import/Export
```
POST   /api/import/gpx                 # Import GPX file
POST   /api/import/kml                 # Import KML file
GET    /api/export/{track_id}/gpx      # Export as GPX
GET    /api/export/{track_id}/geojson  # Export as GeoJSON
```

#### System Health
```
GET    /api/system/health              # Overall system status
GET    /api/system/stats               # Statistics (track count, disk usage)
GET    /api/system/updates             # Available system updates
POST   /api/system/updates             # Trigger system update
```

---

## Background Jobs & Task Management

### Task Queue
- **Celery** with Redis or RabbitMQ
  - Long-running import/export operations
  - Periodic cleanup tasks
  - Map tile pre-generation
  - Database maintenance (VACUUM, ANALYZE)

**Alternative:**
- **APScheduler** (Advanced Python Scheduler)
  - Simpler, embedded scheduler
  - Good for lighter workloads
  - No separate broker required

### Scheduled Tasks
- Periodic database optimization
- Old APRS station cleanup (e.g., >24 hours old)
- Log rotation
- System health checks
- Backup operations (if implemented)

---

## Real-Time Communication

### WebSocket Implementation
**Using FastAPI WebSockets:**
```python
# Real-time GPS position streaming
@app.websocket("/api/gps/stream")
async def gps_stream(websocket: WebSocket):
    await websocket.accept()
    while True:
        position = await get_current_position()
        await websocket.send_json(position)
        await asyncio.sleep(1)
```

### Broadcasting
- **Redis Pub/Sub** - Distribute GPS updates to multiple clients
- **WebSocket Manager** - Track connected clients, broadcast updates

---

## Data Validation & Models

### Pydantic Models
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class GPSPoint(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    elevation: Optional[float] = None
    timestamp: datetime
    speed: Optional[float] = Field(None, ge=0)
    heading: Optional[float] = Field(None, ge=0, le=360)

class Track(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    distance_km: Optional[float] = None
    points: list[GPSPoint] = []
```

---

## Geospatial Libraries & Tools

### Core Libraries
- **Shapely** - Geometric operations (LineString, Point, Polygon)
- **geopy** - Distance calculations, geocoding
- **pyproj** - Coordinate reference system transformations
- **GeoAlchemy2** - SQLAlchemy integration with PostGIS
- **Fiona** - Read/write geospatial file formats

### Spatial Operations
```python
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

# Check if current position is on a new road
current_point = Point(lon, lat)
existing_tracks = query_nearby_tracks(current_point, buffer_meters=100)

if not existing_tracks:
    alert_new_road()
```

---

## Performance Optimization

### Database Optimization
- **Connection Pooling** (SQLAlchemy default)
- **Prepared Statements** for repeated queries
- **Spatial Indexes** (GiST) on all geometric columns
- **BRIN Indexes** for time-series data (track_points.timestamp)
- **Partitioning** for track_points table (by year/month if dataset grows large)

### Query Optimization
```sql
-- Efficient nearby tracks query
SELECT t.id, t.name, ST_Distance(tp.geom, ST_SetSRID(ST_MakePoint($lon, $lat), 4326)) as distance
FROM tracks t
JOIN track_points tp ON t.id = tp.track_id
WHERE ST_DWithin(tp.geom, ST_SetSRID(ST_MakePoint($lon, $lat), 4326), 0.001)
ORDER BY distance
LIMIT 10;
```

### Caching Strategy
- **Redis** for frequently accessed data
  - Current GPS position
  - Active APRS stations
  - Track metadata
- **TTL-based expiration** for real-time data

---

## Testing Strategy

### Testing Framework
- **pytest** - Primary testing framework
- **pytest-asyncio** - For async code testing
- **pytest-cov** - Code coverage
- **httpx** - Async HTTP client for API testing

### Test Categories
1. **Unit Tests** - Individual functions (smart beaconing, distance calculations)
2. **Integration Tests** - Database operations, API endpoints
3. **Performance Tests** - Spatial query performance, import/export speed
4. **Mock Tests** - GPS hardware simulation, APRS packet generation

---

## Logging & Monitoring

### Logging
- **Python logging module** - Standard library
- **structlog** - Structured logging for better analysis
- **Log levels:**
  - DEBUG: GPS point processing
  - INFO: Track creation, API requests
  - WARNING: GPS signal loss, missing data
  - ERROR: Database errors, import failures
  - CRITICAL: System failures

### Monitoring Metrics
- GPS fix quality (satellite count, HDOP)
- Database connection pool status
- API response times
- Track processing throughput
- Disk space usage
- APRS packet reception rate

---

## Security Considerations

### API Security
- **API Key Authentication** (for web interface)
- **Rate Limiting** (slowapi or FastAPI middleware)
- **CORS Configuration** - Restrict origins in production
- **Input Validation** - Pydantic models for all inputs

### Database Security
- **Connection encryption** (SSL/TLS)
- **Prepared statements** to prevent SQL injection
- **Least privilege** database user permissions
- **Regular backups** (pg_dump scheduled tasks)

---

## Development Tools

### Code Quality
- **black** - Code formatting
- **flake8** or **ruff** - Linting
- **mypy** - Type checking
- **pre-commit hooks** - Automated checks before commits

### Documentation
- **Sphinx** - API documentation generation
- **mkdocs** - Project documentation
- **FastAPI automatic docs** - OpenAPI/Swagger UI at `/docs`

---

## Recommended Full Stack

```
Operating System: Raspberry Pi OS (64-bit) or Ubuntu Server

Backend Application:
├── FastAPI (web framework)
├── Uvicorn (ASGI server)
├── SQLAlchemy + GeoAlchemy2 (ORM)
├── Alembic (database migrations)
├── Pydantic (data validation)
└── Python 3.11+

Database:
├── PostgreSQL 15+
└── PostGIS 3.3+

Data Processing:
├── Shapely (geometric operations)
├── geopy (distance/bearing calculations)
├── gpxpy (GPX import/export)
├── fastkml (KML import/export)
├── aprslib (APRS parsing)
└── pyproj (coordinate transformations)

Task Management:
├── Celery (background jobs) - OR
└── APScheduler (lightweight alternative)

Caching/Message Queue:
└── Redis (optional but recommended)

Testing:
├── pytest
├── pytest-asyncio
├── pytest-cov
└── httpx

Code Quality:
├── black (formatting)
├── ruff (linting)
├── mypy (type checking)
└── pre-commit (automation)
```

---

## Performance Targets

### Response Time Goals
- GPS current position: < 100ms
- Track list query: < 500ms
- Nearby tracks query: < 1 second
- Track detail with points: < 2 seconds
- Import 10,000 point GPX: < 30 seconds
- Export GPX: < 5 seconds

### Database Performance
- Track point insertion: > 1000 points/second
- Spatial queries: < 500ms for 1 million points
- New road detection: < 200ms

---

## Deployment Considerations

### Service Configuration
```ini
# systemd service for backend API
[Unit]
Description=GPS Carputer Backend API
After=network.target postgresql.service

[Service]
Type=notify
User=pi
WorkingDirectory=/opt/carputer/backend
ExecStart=/opt/carputer/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Process Management
- **Uvicorn** with multiple workers (--workers 2-4)
- **Gunicorn** alternative with uvicorn workers
- **Supervisor** for process monitoring (alternative to systemd)

---

## Database Schema Example

```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Tracks table
CREATE TABLE tracks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    distance_km NUMERIC(10, 3),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Track points with geometry
CREATE TABLE track_points (
    id BIGSERIAL PRIMARY KEY,
    track_id INTEGER REFERENCES tracks(id) ON DELETE CASCADE,
    geom GEOMETRY(Point, 4326) NOT NULL,
    elevation NUMERIC(8, 2),
    timestamp TIMESTAMP NOT NULL,
    speed NUMERIC(6, 2),
    heading NUMERIC(5, 2),
    hdop NUMERIC(4, 2)
);

-- Spatial index on track points
CREATE INDEX idx_track_points_geom ON track_points USING GIST(geom);
CREATE INDEX idx_track_points_timestamp ON track_points USING BRIN(timestamp);
CREATE INDEX idx_track_points_track_id ON track_points(track_id);

-- Road segments for new road detection
CREATE TABLE road_segments (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(LineString, 4326) NOT NULL,
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    visit_count INTEGER DEFAULT 1,
    metadata JSONB
);

CREATE INDEX idx_road_segments_geom ON road_segments USING GIST(geometry);

-- APRS stations
CREATE TABLE aprs_stations (
    callsign VARCHAR(9) PRIMARY KEY,
    geom GEOMETRY(Point, 4326) NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    symbol VARCHAR(2),
    comment TEXT,
    metadata JSONB
);

CREATE INDEX idx_aprs_stations_geom ON aprs_stations USING GIST(geom);
CREATE INDEX idx_aprs_stations_last_seen ON aprs_stations(last_seen);

-- APRS history for time-series tracking
CREATE TABLE aprs_history (
    id BIGSERIAL PRIMARY KEY,
    callsign VARCHAR(9) NOT NULL,
    geom GEOMETRY(Point, 4326) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    raw_packet TEXT,
    FOREIGN KEY (callsign) REFERENCES aprs_stations(callsign)
);

CREATE INDEX idx_aprs_history_callsign ON aprs_history(callsign);
CREATE INDEX idx_aprs_history_timestamp ON aprs_history USING BRIN(timestamp);
```

---

## Migration Strategy

### Database Migrations with Alembic
```bash
# Initialize Alembic
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## Next Steps

1. **Set up development environment**
   - Install PostgreSQL with PostGIS
   - Create Python virtual environment
   - Install core dependencies

2. **Database schema implementation**
   - Create initial migration
   - Set up spatial indexes
   - Test spatial queries

3. **Core API development**
   - Implement track CRUD endpoints
   - GPS position streaming
   - APRS data ingestion

4. **Smart beaconing implementation**
   - Algorithm development and testing
   - Integration with GPS data pipeline

5. **New road detection logic**
   - Spatial query optimization
   - Alert mechanism implementation

6. **Import/Export functionality**
   - GPX parser implementation
   - Multi-format support
   - Validation and error handling

7. **Testing & optimization**
   - Unit and integration tests
   - Performance benchmarking
   - Query optimization

---

## Additional Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **PostGIS Documentation:** https://postgis.net/documentation/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **Shapely Documentation:** https://shapely.readthedocs.io/
- **APRS Protocol Reference:** http://www.aprs.org/doc/APRS101.PDF
- **Smart Beaconing Algorithm:** http://www.hamhud.net/hh2/smartbeacon.html
