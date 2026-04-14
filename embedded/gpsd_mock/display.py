"""Connect to a gpsd (or mock gpsd) and display live GPS data.

Usage:
    python -m gpsd_mock.display              # default localhost:2947
    python -m gpsd_mock.display --port 2947
"""

import argparse
import json
import socket
import sys
from datetime import datetime

MPS_TO_MPH = 2.23694

# Compass rose for heading
_COMPASS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


def _bearing_to_compass(deg: float) -> str:
    idx = round(deg / 22.5) % 16
    return _COMPASS[idx]


def _clear_line():
    sys.stdout.write("\033[2K\r")


def _send_line(sock: socket.socket, text: str):
    sock.sendall((text + "\r\n").encode())


def _read_json(f) -> dict:
    line = f.readline()
    if not line:
        raise ConnectionError("Server closed connection")
    return json.loads(line)


def _handshake(sock: socket.socket, f):
    """Perform the gpsd connect handshake and return VERSION info."""
    version = _read_json(f)
    _read_json(f)  # DEVICES
    _send_line(sock, '?WATCH={"enable":true,"json":true};')
    _read_json(f)  # WATCH echo
    return version


def _format_tpv(tpv: dict) -> str:
    lat = tpv.get("lat", 0.0)
    lon = tpv.get("lon", 0.0)
    speed_mps = tpv.get("speed", 0.0)
    speed_mph = speed_mps * MPS_TO_MPH
    heading = tpv.get("track", 0.0)
    compass = _bearing_to_compass(heading)
    alt = tpv.get("altHAE", 0.0)
    ts = tpv.get("time", "")

    return (
        f"  {lat:>11.6f}°, {lon:>12.6f}°  "
        f"| {speed_mph:5.1f} mph {compass:>3s} ({heading:05.1f}°)  "
        f"| alt {alt:6.1f}m  "
        f"| {ts}"
    )


def main():
    parser = argparse.ArgumentParser(description="gpsd intake display")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2947)
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)

    print(f"Connecting to gpsd at {args.host}:{args.port} ...")
    try:
        sock.connect((args.host, args.port))
    except ConnectionRefusedError:
        print(f"Error: could not connect to {args.host}:{args.port}")
        print("Is the mock server running?  python -m gpsd_mock")
        sys.exit(1)

    f = sock.makefile()
    version = _handshake(sock, f)
    release = version.get("release", "?")
    print(f"Connected — gpsd {release} (proto {version.get('proto_major', '?')}.{version.get('proto_minor', '?')})")
    print()
    print("  Latitude      Longitude       Speed         Heading          Alt        Time")
    print("  " + "─" * 90)

    count = 0
    try:
        while True:
            msg = _read_json(f)
            if msg.get("class") != "TPV":
                continue
            count += 1
            line = _format_tpv(msg)
            print(line)
    except KeyboardInterrupt:
        print(f"\n\nReceived {count} fixes. Goodbye.")
    except ConnectionError:
        print(f"\nConnection lost after {count} fixes.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
