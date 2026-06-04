"""Mock APRS station generator for demo purposes."""

import random
import time
import requests
from dataclasses import dataclass
from typing import List

# API endpoint - core-api on port 8888
API_URL = "http://localhost:8888/v2/aprs/ingest"

@dataclass
class MockStation:
    callsign: str
    lat: float
    lon: float
    symbol_table: str  # "/" for primary, "\\" for alternate
    symbol_code: str   # single char like "k" for truck, "-" for house
    comment: str


# Mock stations around the PSU demo route
MOCK_STATIONS: List[MockStation] = [
    MockStation("W7PDX-9", 45.5118, -122.6825, "/", "k", "Mobile - Downtown"),
    MockStation("KG7ABC-1", 45.5130, -122.6790, "/", "-", "Home Station"),
    MockStation("N7XYZ-5", 45.5095, -122.6810, "/", "#", "Digipeater"),
    MockStation("WA7PDX-2", 45.5105, -122.6850, "/", "r", "Repeater 147.04"),
    MockStation("K7PSU", 45.5115, -122.6800, "/", "Y", "PSU Radio Club"),
    MockStation("W7BPD-9", 45.5090, -122.6830, "/", ">", "Mobile unit"),
]


def send_position(station: MockStation) -> bool:
    """Send a position report to the API."""
    # Format matching UpsertAPRSStationRequest
    payload = {
        "callsign": station.callsign,
        "latitude": station.lat,
        "longitude": station.lon,
        "altitude_m": 50.0,  # ~164 ft, typical for Portland
        "course_deg": random.uniform(0, 360),
        "speed_knots": random.uniform(0, 25),  # 0-25 knots for stationary/moving
        "symbol_table": station.symbol_table,
        "symbol_code": station.symbol_code,
        "comment": station.comment,
        "raw_packet": f"{station.callsign}>APRS,TCPIP*:!{abs(station.lat)*100:.2f}N/{abs(station.lon)*100:.2f}W{station.symbol_code}{station.comment}",
    }
    
    try:
        resp = requests.post(API_URL, json=payload, timeout=5)
        if resp.status_code in (200, 201):
            return True
        else:
            print(f"Failed to send {station.callsign}: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"Error sending {station.callsign}: {e}")
        return False


def main():
    """Send mock APRS positions periodically."""
    print("Mock APRS Station Generator")
    print(f"Sending {len(MOCK_STATIONS)} stations to {API_URL}")
    print("Press Ctrl+C to stop\n")
    
    while True:
        for station in MOCK_STATIONS:
            # Add slight position jitter to simulate movement
            jittered = MockStation(
                callsign=station.callsign,
                lat=station.lat + random.uniform(-0.0002, 0.0002),
                lon=station.lon + random.uniform(-0.0002, 0.0002),
                symbol_table=station.symbol_table,
                symbol_code=station.symbol_code,
                comment=station.comment,
            )
            success = send_position(jittered)
            if success:
                print(f"✓ {station.callsign}")
        
        print(f"\n--- Sleeping 30s before next update ---\n")
        time.sleep(30)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped")
