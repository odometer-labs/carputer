#!/usr/bin/env python3
"""
Generates a Portland-area NMEA route file for demo/mock GPS playback.

Route: PSU → Pioneer Courthouse Square → NW 23rd → Hawthorne → PSU
Approx 7.5 miles of city driving at ~20 mph.
"""

import math
import os

OUTPUT = os.path.join(
    os.path.dirname(__file__),
    "../frontend/carputer-web-app/src/fake-api/portland-loop.nmea",
)

# Waypoints: (lat, lon, label)
WAYPOINTS = [
    (45.5147, -122.6819, "PSU"),
    (45.5193, -122.6784, "SW Broadway & Market"),
    (45.5231, -122.6784, "Pioneer Courthouse Square"),
    (45.5242, -122.6831, "W Burnside & 10th"),
    (45.5265, -122.6950, "W Burnside & NW 21st"),
    (45.5272, -122.7003, "NW 23rd & Burnside"),
    (45.5220, -122.7003, "NW 23rd & Lovejoy"),
    (45.5196, -122.6999, "NW 23rd & Marshall"),
    (45.5147, -122.6999, "SW 23rd & Jefferson"),
    (45.5147, -122.6868, "SW Jefferson & 11th"),
    (45.5122, -122.6819, "SW Harrison & Park"),
    (45.5082, -122.6784, "SW 3rd & College"),
    (45.5082, -122.6658, "OMSI area"),
    (45.5122, -122.6658, "SE Grand & Morrison"),
    (45.5122, -122.6723, "Hawthorne Bridge east"),
    (45.5120, -122.6780, "Hawthorne Bridge west"),
    (45.5147, -122.6819, "PSU"),  # close the loop
]

SPEED_MPH = 20.0
SPEED_KNOTS = SPEED_MPH * 0.868976
POINTS_PER_SEGMENT = 60  # ~60 points between each waypoint pair


def nmea_checksum(sentence: str) -> str:
    """XOR checksum of all chars between $ and * (exclusive)."""
    val = 0
    for ch in sentence:
        val ^= ord(ch)
    return f"{val:02X}"


def decimal_to_nmea_lat(lat: float) -> tuple[str, str]:
    """Convert decimal degrees latitude to NMEA DDMM.MMMM format + direction."""
    direction = "N" if lat >= 0 else "S"
    lat = abs(lat)
    degrees = int(lat)
    minutes = (lat - degrees) * 60
    return f"{degrees:02d}{minutes:07.4f}", direction


def decimal_to_nmea_lon(lon: float) -> tuple[str, str]:
    """Convert decimal degrees longitude to NMEA DDDMM.MMMM format + direction."""
    direction = "E" if lon >= 0 else "W"
    lon = abs(lon)
    degrees = int(lon)
    minutes = (lon - degrees) * 60
    return f"{degrees:03d}{minutes:07.4f}", direction


def bearing(lat1, lon1, lat2, lon2) -> float:
    """Initial bearing in degrees from point 1 to point 2."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def interpolate(p1, p2, steps):
    """Linearly interpolate steps points between p1 and p2 (exclusive of p1, inclusive of p2)."""
    lat1, lon1 = p1
    lat2, lon2 = p2
    return [
        (lat1 + (lat2 - lat1) * i / steps, lon1 + (lon2 - lon1) * i / steps)
        for i in range(1, steps + 1)
    ]


def make_gprmc(lat, lon, speed_knots, course, time_s) -> str:
    h = int(time_s // 3600) % 24
    m = int((time_s % 3600) // 60)
    s = time_s % 60
    time_str = f"{h:02d}{m:02d}{s:05.2f}"
    lat_str, lat_dir = decimal_to_nmea_lat(lat)
    lon_str, lon_dir = decimal_to_nmea_lon(lon)
    body = f"GPRMC,{time_str},A,{lat_str},{lat_dir},{lon_str},{lon_dir},{speed_knots:.1f},{course:.1f},010625,000.0,W"
    return f"${body}*{nmea_checksum(body)}"


def main():
    lines = []
    time_s = 28800  # start at 08:00:00

    all_points = []
    for i in range(len(WAYPOINTS) - 1):
        p1 = WAYPOINTS[i][:2]
        p2 = WAYPOINTS[i + 1][:2]
        segment_points = interpolate(p1, p2, POINTS_PER_SEGMENT)
        course = bearing(*p1, *p2)
        for pt in segment_points:
            all_points.append((pt[0], pt[1], course))

    for lat, lon, course in all_points:
        sentence = make_gprmc(lat, lon, SPEED_KNOTS, course, time_s)
        lines.append(sentence)
        time_s += 1  # one point per second

    out_path = os.path.normpath(OUTPUT)
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Written {len(lines)} NMEA sentences to {out_path}")
    print(f"Route duration: ~{len(lines) // 60} minutes")


if __name__ == "__main__":
    main()
