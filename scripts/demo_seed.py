#!/usr/bin/env python3
"""
Carputer Demo Seed Script
=========================
Seeds the running carputer API with:
  - 7 mock APRS stations around Portland, OR
  - 3 historical GPX tracks (pre-recorded Portland drives)

Usage:
    python3 scripts/demo_seed.py [--api http://localhost:8000]

The API must be running before you run this script.
"""

import argparse
import json
import sys
import textwrap
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    sys.exit("requests is not installed. Run: pip install requests")

# ---------------------------------------------------------------------------
# APRS stations — realistic Portland-area ham radio stations
# ---------------------------------------------------------------------------
# Symbol table "/" + code reference: https://aprs.org/symbols.html
# "k" = truck, "-" = house, ">" = car, "O" = balloon, "[" = human, "r" = repeater

APRS_STATIONS = [
    {
        "callsign": "W7PDX-1",
        "latitude": 45.4938,
        "longitude": -122.7117,
        "symbol_table": "/",
        "symbol_code": "r",  # repeater
        "comment": "Council Crest Repeater 146.840-",
        "altitude_m": 283.0,
        "speed_knots": None,
        "course_deg": None,
    },
    {
        "callsign": "KD7TRK-9",
        "latitude": 45.5119,
        "longitude": -122.5948,
        "symbol_table": "/",
        "symbol_code": "k",  # truck/mobile
        "comment": "Mt. Tabor mobile",
        "altitude_m": 185.0,
        "speed_knots": 0.0,
        "course_deg": 90.0,
    },
    {
        "callsign": "N7PDX-2",
        "latitude": 45.5594,
        "longitude": -122.5711,
        "symbol_table": "/",
        "symbol_code": "r",  # repeater
        "comment": "Rocky Butte Digi/IGate",
        "altitude_m": 220.0,
        "speed_knots": None,
        "course_deg": None,
    },
    {
        "callsign": "KG7OMC-7",
        "latitude": 45.5082,
        "longitude": -122.6658,
        "symbol_table": "/",
        "symbol_code": "-",  # house/fixed
        "comment": "OMSI fixed station",
        "altitude_m": 15.0,
        "speed_knots": None,
        "course_deg": None,
    },
    {
        "callsign": "W7VJG-4",
        "latitude": 45.5271,
        "longitude": -122.6835,
        "symbol_table": "/",
        "symbol_code": "-",  # house/fixed
        "comment": "NW Portland home station",
        "altitude_m": 55.0,
        "speed_knots": None,
        "course_deg": None,
    },
    {
        "callsign": "KF7RZX-9",
        "latitude": 45.5220,
        "longitude": -122.7003,
        "symbol_table": "/",
        "symbol_code": ">",  # car
        "comment": "NW 23rd mobile enroute",
        "altitude_m": 60.0,
        "speed_knots": 15.2,
        "course_deg": 195.0,
    },
    {
        "callsign": "WB7QMR-3",
        "latitude": 45.4867,
        "longitude": -122.6036,
        "symbol_table": "/",
        "symbol_code": "[",  # human/walker
        "comment": "Sellwood hiker",
        "altitude_m": 30.0,
        "speed_knots": 1.5,
        "course_deg": 45.0,
    },
]

# ---------------------------------------------------------------------------
# Historical GPX tracks — three Portland drives
# ---------------------------------------------------------------------------

def make_gpx(name: str, points: list[tuple[float, float]]) -> str:
    """Build a minimal valid GPX 1.1 string from a list of (lat, lon) tuples."""
    now = datetime.now(timezone.utc).isoformat()
    trkpts = "\n      ".join(
        f'<trkpt lat="{lat}" lon="{lon}"><time>{now}</time></trkpt>'
        for lat, lon in points
    )
    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <gpx version="1.1" creator="carputer-demo"
             xmlns="http://www.topografix.com/GPX/1/1">
          <trk>
            <name>{name}</name>
            <trkseg>
              {trkpts}
            </trkseg>
          </trk>
        </gpx>
        """)


# Route 1: Morning commute — Beaverton TC → PSU via Barbur
BEAVERTON_TO_PSU = [
    (45.4876, -122.8032), (45.4892, -122.7980), (45.4917, -122.7901),
    (45.4944, -122.7823), (45.4972, -122.7740), (45.5000, -122.7665),
    (45.5022, -122.7591), (45.5047, -122.7520), (45.5068, -122.7444),
    (45.5088, -122.7370), (45.5105, -122.7295), (45.5118, -122.7223),
    (45.5130, -122.7150), (45.5138, -122.7075), (45.5142, -122.7000),
    (45.5144, -122.6930), (45.5145, -122.6875), (45.5147, -122.6819),
]

# Route 2: Afternoon — PSU → Ladd's Addition → Sellwood Riverfront
PSU_TO_SELLWOOD = [
    (45.5147, -122.6819), (45.5122, -122.6784), (45.5100, -122.6730),
    (45.5082, -122.6658), (45.5064, -122.6608), (45.5047, -122.6560),
    (45.5020, -122.6540), (45.4993, -122.6522), (45.4966, -122.6504),
    (45.4940, -122.6612), (45.4920, -122.6658), (45.4900, -122.6705),
    (45.4878, -122.6674), (45.4860, -122.6636), (45.4845, -122.6590),
]

# Route 3: Weekend — PSU → Pearl District → Fremont Bridge → North Portland
PSU_TO_NORTH = [
    (45.5147, -122.6819), (45.5180, -122.6819), (45.5215, -122.6819),
    (45.5231, -122.6850), (45.5248, -122.6880), (45.5265, -122.6880),
    (45.5282, -122.6850), (45.5300, -122.6820), (45.5318, -122.6790),
    (45.5338, -122.6750), (45.5358, -122.6708), (45.5375, -122.6670),
    (45.5392, -122.6630), (45.5408, -122.6590), (45.5425, -122.6550),
    (45.5440, -122.6510), (45.5454, -122.6470), (45.5465, -122.6435),
]

TRACKS = [
    ("Morning Commute — Beaverton to PSU", BEAVERTON_TO_PSU),
    ("Afternoon Drive — PSU to Sellwood", PSU_TO_SELLWOOD),
    ("Weekend — PSU to North Portland via Pearl", PSU_TO_NORTH),
]


# ---------------------------------------------------------------------------
# Seeding functions
# ---------------------------------------------------------------------------

def seed_aprs(base_url: str) -> None:
    print("\n=== Seeding APRS stations ===")
    url = f"{base_url}/v1/aprs/ingest"
    for station in APRS_STATIONS:
        payload = {k: v for k, v in station.items() if v is not None}
        try:
            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()
            print(f"  ✓ {station['callsign']} ({station['comment']})")
        except requests.HTTPError as e:
            print(f"  ✗ {station['callsign']}: HTTP {e.response.status_code} — {e.response.text[:120]}")
        except requests.ConnectionError:
            print(f"  ✗ {station['callsign']}: connection refused — is the API running at {base_url}?")
            sys.exit(1)


def seed_tracks(base_url: str) -> None:
    print("\n=== Importing historical GPX tracks ===")
    url = f"{base_url}/v1/tracks/import/gpx"
    for name, points in TRACKS:
        gpx_bytes = make_gpx(name, points).encode()
        filename = name.replace(" ", "_").replace("—", "-") + ".gpx"
        try:
            r = requests.post(
                url,
                files={"file": (filename, gpx_bytes, "application/gpx+xml")},
                timeout=10,
            )
            r.raise_for_status()
            print(f"  ✓ {name}")
        except requests.HTTPError as e:
            print(f"  ✗ {name}: HTTP {e.response.status_code} — {e.response.text[:120]}")
        except requests.ConnectionError:
            print(f"  ✗ {name}: connection refused — is the API running at {base_url}?")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Seed carputer demo data")
    parser.add_argument(
        "--api",
        default="http://localhost:8000",
        help="Base URL of the carputer API (default: http://localhost:8000)",
    )
    args = parser.parse_args()
    base_url = args.api.rstrip("/")

    print(f"Seeding demo data → {base_url}")
    seed_aprs(base_url)
    seed_tracks(base_url)
    print("\nDone! Start the in-car app and you should see APRS stations on the map.")
    print("Use the remote web interface → Manage Data to view and export the tracks.")


if __name__ == "__main__":
    main()
