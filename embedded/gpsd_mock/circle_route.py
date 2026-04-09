"""Generate positions along a circular route around a center point."""

import math


class CircleRoute:
    """Produces (lat, lon, speed, heading) for a point moving in a circle.

    The circle is defined by a center coordinate and radius. The point
    moves counter-clockwise at a constant speed, starting due East of
    the center at t=0.
    """

    MI_TO_M = 1609.344
    EARTH_RADIUS_M = 6371000.0

    def __init__(
        self,
        center_lat: float,
        center_lon: float,
        radius_mi: float,
        speed_mps: float = 5.0,
    ):
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.radius_m = radius_mi * self.MI_TO_M
        self.speed_mps = speed_mps

    @property
    def circumference_m(self) -> float:
        return 2.0 * math.pi * self.radius_m

    @property
    def period_seconds(self) -> float:
        """Time in seconds to complete one full loop."""
        return self.circumference_m / self.speed_mps

    @property
    def angular_velocity(self) -> float:
        """Radians per second."""
        return 2.0 * math.pi / self.period_seconds

    def position_at(self, t: float) -> dict:
        """Return position dict at elapsed time *t* seconds.

        Returns dict with keys: lat, lon, speed, heading.
        """
        angle = self.angular_velocity * t  # radians, 0 = East, CCW

        # Offset in meters from center
        dx = self.radius_m * math.cos(angle)  # East
        dy = self.radius_m * math.sin(angle)  # North

        # Convert meter offsets to lat/lon deltas
        dlat = dy / self.EARTH_RADIUS_M  # radians
        dlon = dx / (
            self.EARTH_RADIUS_M * math.cos(math.radians(self.center_lat))
        )  # radians

        lat = self.center_lat + math.degrees(dlat)
        lon = self.center_lon + math.degrees(dlon)

        # Heading: tangent to the circle. For CCW motion the velocity
        # vector is 90° ahead of the position angle.
        # velocity direction angle (math convention, from East CCW):
        vel_angle = angle + math.pi / 2  # perpendicular to radius, CCW
        # Convert to compass bearing (0=N, CW):
        bearing = (90.0 - math.degrees(vel_angle)) % 360.0

        return {
            "lat": lat,
            "lon": lon,
            "speed": self.speed_mps,
            "heading": bearing,
        }
