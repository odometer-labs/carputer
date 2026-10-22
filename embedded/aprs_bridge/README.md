# APRS Bridge

Connects Direwolf's KISS TCP interface to the Carputer FastAPI backend.

## Architecture

```
┌─────────────┐     ┌───────────────┐     ┌─────────────┐     ┌──────────────┐
│  RTL-SDR    │────►│   rtl_fm      │────►│  Direwolf   │────►│ APRS Bridge  │
│  Antenna    │     │ FM demod      │     │  KISS:8003  │     │  (this)      │
└─────────────┘     └───────────────┘     └─────────────┘     └──────┬───────┘
                                                                     │
                                                                     ▼
                                                              ┌──────────────┐
                                                              │   Backend    │
                                                              │ FastAPI:8000 │
                                                              └──────────────┘
```

## Requirements

- Python 3.9+
- `requests` library
- Direwolf running with KISS TCP enabled on port 8003

## Installation

```bash
pip install requests
```

## Usage

### As a Python module

```bash
cd /path/to/carputer/embedded
python -m aprs_bridge
```

### With custom settings

```bash
KISS_HOST=192.168.1.100 \
KISS_PORT=8003 \
BACKEND_URL=http://localhost:8000 \
python -m aprs_bridge
```

### As a systemd service

See `/infrastructure/systemd/` for service files.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KISS_HOST` | `localhost` | Direwolf host |
| `KISS_PORT` | `8003` | Direwolf KISS TCP port |
| `BACKEND_URL` | `http://localhost:8000` | FastAPI backend URL |
| `RECONNECT_DELAY` | `5.0` | Seconds between reconnect attempts |
| `APRS_LOG_FILE` | `/var/log/carputer/aprs-bridge.log` | Log file path |
| `APRS_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |

## Supported APRS Formats

- **Uncompressed position** (`!`, `=`, `/`, `@`)
- **Compressed position** (base91 encoding)
- **Mic-E encoded position** (destination address encoding)

## API Endpoints Used

The bridge sends parsed packets to:

```
POST /v1/aprs/ingest
```

With payload:
```json
{
  "callsign": "W1ABC-10",
  "latitude": 42.3601,
  "longitude": -71.0589,
  "symbol_table": "/",
  "symbol_code": "k",
  "comment": "Mobile",
  "altitude_m": 100.0,
  "speed_knots": 55.0,
  "course_deg": 180.0,
  "raw_packet": "W1ABC-10>APRS,WIDE1-1:!4221.61N/07103.53W-Mobile"
}
```

## Testing

### Mock APRS packets

You can inject test packets directly to the backend:

```bash
curl -X POST http://localhost:8000/v1/aprs/ingest-raw \
  -H "Content-Type: application/json" \
  -d '{"raw_packet": "W1ABC>APRS:!4221.61N/07103.53W-Test"}'
```

### Check ingested stations

```bash
curl http://localhost:8000/v1/aprs/stations
```
