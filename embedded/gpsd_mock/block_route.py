"""Generate positions along a rectangular route around city blocks."""

import math
from typing import List, Tuple


class BlockRoute:
    """Produces (lat, lon, speed, heading) for a point moving around city blocks.

    The route follows a rectangular path defined by corner coordinates,
    simulating driving around a few city blocks in downtown Portland.
    """

    EARTH_RADIUS_M = 6371000.0

    def __init__(
        self,
        waypoints: List[Tuple[float, float]] | None = None,
        speed_mps: float = 8.0,  # ~18 mph, typical city driving
    ):
        """Initialize with a list of (lat, lon) waypoints forming a closed loop.
        
        If no waypoints provided, defaults to a loop around PSU in downtown Portland.
        """
        if waypoints is None:
            # Loop around blocks near PSU following actual streets
            # Route: SW 6th Ave → SW Market St → SW Broadway → SW Mill St → back to 6th
            waypoints = [
                # North side - heading east on SW Market St
                (45.51215, -122.68135),  # SW 6th & Market (start)
                (45.51215, -122.68050),  # SW 5th & Market
                (45.51215, -122.67965),  # SW 4th & Market
                (45.51215, -122.67880),  # SW Broadway & Market
                
                # East side - heading south on SW Broadway
                (45.51125, -122.67880),  # SW Broadway & Mill
                (45.51035, -122.67880),  # SW Broadway & Harrison
                (45.50945, -122.67880),  # SW Broadway & Hall
                
                # South side - heading west on SW Hall St
                (45.50945, -122.67965),  # SW 4th & Hall
                (45.50945, -122.68050),  # SW 5th & Hall
                (45.50945, -122.68135),  # SW 6th & Hall
                
                # West side - heading north on SW 6th Ave
                (45.51035, -122.68135),  # SW 6th & Harrison
                (45.51125, -122.68135),  # SW 6th & Mill
            ]
        
        self.waypoints = waypoints
        self.speed_mps = speed_mps
        
        # Pre-calculate segment lengths and total perimeter
        self._segments = self._calculate_segments()
        self._total_length = sum(seg["length"] for seg in self._segments)

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in meters between two coordinates."""
        lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
        lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
        
        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return self.EARTH_RADIUS_M * c

    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate compass bearing from point 1 to point 2."""
        lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
        lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
        
        dlon = lon2_r - lon1_r
        
        x = math.sin(dlon) * math.cos(lat2_r)
        y = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon)
        
        bearing = math.atan2(x, y)
        return (math.degrees(bearing) + 360) % 360

    def _calculate_segments(self) -> List[dict]:
        """Pre-calculate segment info: start, end, length, bearing."""
        segments = []
        n = len(self.waypoints)
        
        for i in range(n):
            start = self.waypoints[i]
            end = self.waypoints[(i + 1) % n]
            
            length = self._haversine_distance(start[0], start[1], end[0], end[1])
            bearing = self._calculate_bearing(start[0], start[1], end[0], end[1])
            
            segments.append({
                "start": start,
                "end": end,
                "length": length,
                "bearing": bearing,
            })
        
        return segments

    @property
    def perimeter_m(self) -> float:
        """Total route length in meters."""
        return self._total_length

    @property
    def period_seconds(self) -> float:
        """Time in seconds to complete one full loop."""
        return self._total_length / self.speed_mps

    def position_at(self, t: float) -> dict:
        """Return position dict at elapsed time *t* seconds.

        Returns dict with keys: lat, lon, speed, heading.
        """
        # Distance traveled (mod total length for looping)
        distance = (self.speed_mps * t) % self._total_length
        
        # Find which segment we're on
        accumulated = 0.0
        for seg in self._segments:
            if accumulated + seg["length"] > distance:
                # We're on this segment
                segment_progress = distance - accumulated
                fraction = segment_progress / seg["length"]
                
                # Interpolate position
                lat = seg["start"][0] + fraction * (seg["end"][0] - seg["start"][0])
                lon = seg["start"][1] + fraction * (seg["end"][1] - seg["start"][1])
                
                return {
                    "lat": lat,
                    "lon": lon,
                    "speed": self.speed_mps,
                    "heading": seg["bearing"],
                }
            accumulated += seg["length"]
        
        # Fallback (shouldn't reach here)
        return {
            "lat": self.waypoints[0][0],
            "lon": self.waypoints[0][1],
            "speed": self.speed_mps,
            "heading": self._segments[0]["bearing"],
        }
