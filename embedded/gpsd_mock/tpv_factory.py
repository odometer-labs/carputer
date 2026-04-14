"""Build gpsd-compatible TPV JSON dicts."""

from datetime import datetime, timezone


def make_tpv(
    lat: float,
    lon: float,
    speed: float,
    heading: float,
    time: datetime | None = None,
    device: str = "/dev/ttyACM0",
    altitude: float = 15.0,
) -> dict:
    """Create a gpsd TPV message dict.

    Args:
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        speed: Speed over ground in m/s.
        heading: Heading in degrees (0-360, 0=North).
        time: Timestamp (defaults to now UTC).
        device: Device path string.
        altitude: Altitude HAE in meters.
    """
    if time is None:
        time = datetime.now(timezone.utc)

    return {
        "class": "TPV",
        "device": device,
        "mode": 3,
        "status": 8,  # Simulated
        "time": time.isoformat(),
        "lat": lat,
        "lon": lon,
        "altHAE": altitude,
        "speed": speed,
        "track": heading,
        "eph": 1.0,
        "epv": 2.0,
    }
