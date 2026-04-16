# gpsd_mock — Mock GPS Daemon

A drop-in mock for the [gpsd](https://gpsd.gitlab.io/gpsd/) TCP daemon. Serves fake TPV (Time-Position-Velocity) JSON messages over a TCP socket, following the real gpsd protocol. The simulated position moves in a 0.5-mile radius circle around Portland State University (45.5104, -122.68365).

This allows backend and frontend developers to work without access to the Raspberry Pi or a real GPS module.

## Quick Start

```bash
cd embedded
python -m gpsd_mock
```

The server starts on port 2947 (the standard gpsd port). Any gpsd client library (`gpsdclient`, `gpspipe`, etc.) can connect to it as if it were a real daemon.

> **Note:** Stop `gpsd.service` and `gpsd.socket` first if they're running, since they also bind port 2947:
> ```bash
> sudo systemctl stop gpsd.socket gpsd.service
> ```

## Options

```
python -m gpsd_mock [--host HOST] [--port PORT] [--interval SECONDS] [--speed M/S]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `2947` | TCP port |
| `--interval` | `1.0` | Seconds between TPV messages |
| `--speed` | `5.0` | Simulated speed in m/s (~11 mph) |

## Display Client

A built-in display client connects to the mock (or any gpsd) and prints live position data:

```bash
python -m gpsd_mock.display
python -m gpsd_mock.display --host localhost --port 2947
```

Sample output:
```
Connected — gpsd 3.25 (proto 3.15)

  Latitude      Longitude       Speed         Heading          Alt        Time
  ──────────────────────────────────────────────────────────────────────────────
    45.510400°,  -122.673324°  |  11.2 mph   N (360.0°)  | alt   15.0m  | 2026-04-09T17:19:40+00:00
    45.510422°,  -122.673324°  |  11.2 mph   N (359.8°)  | alt   15.0m  | 2026-04-09T17:19:41+00:00
```

## Using with Docker Compose

When running the full stack with `docker compose up`, the `gpsd-service` container needs to reach the mock running on your host machine. The `docker-compose.yml` is already configured for this:

1. Start the mock on your host:
   ```bash
   cd embedded && source .venv/bin/activate
   python -m gpsd_mock
   ```

2. In another terminal, start Docker services:
   ```bash
   docker compose up --build
   ```

The `gpsd-service` container connects to your host via `extra_hosts: host-gateway` and the `GPSD_HOST` environment variable.

## Protocol

The server implements the standard gpsd TCP protocol:

1. **Client connects** → server sends `VERSION` and `DEVICES` messages
2. **Client sends** `?WATCH={"enable":true,"json":true};`
3. **Server echoes** `WATCH` confirmation
4. **Server streams** TPV messages at the configured interval

Example TPV message:
```json
{"class":"TPV","device":"/dev/ttyACM0","mode":3,"status":8,"time":"2026-04-09T12:00:00+00:00","lat":45.5104,"lon":-122.67332,"altHAE":15.0,"speed":5.0,"track":360.0,"eph":1.0,"epv":2.0}
```

Key fields consumed by the backend:
- `lat` / `lon` — WGS84 coordinates
- `speed` — meters per second
- `track` — heading in degrees (0-360, 0=North)

## Module Structure

```
gpsd_mock/
├── __init__.py
├── __main__.py        # CLI entry point
├── circle_route.py    # Circular route math (lat/lon/speed/heading at time t)
├── display.py         # Intake display client
├── server.py          # TCP server implementing gpsd protocol
├── tpv_factory.py     # Builds gpsd-format TPV JSON dicts
└── Dockerfile         # Container image for docker-compose
```

## Tests

```bash
cd embedded && source .venv/bin/activate
python -m pytest tests/test_circle_route.py tests/test_tpv_factory.py tests/test_gpsd_server.py tests/test_display.py -v
```
