"""
Smart Beaconing Algorithm for GPS Track Recording

Implements the APRS SmartBeaconing™ algorithm to intelligently decide when to
record GPS track points. This reduces storage requirements while maintaining
accurate route representation by:

- Recording more frequently at higher speeds
- Recording immediately on significant heading changes (turns)
- Recording at regular intervals when stationary or slow-moving

Reference: http://www.hamhud.net/hh2/smartbeacon.html
"""

import time
from dataclasses import dataclass, field
from typing import Optional, Tuple
from math import radians, cos, sin, sqrt, atan2


@dataclass
class BeaconConfig:
    """Configuration parameters for smart beaconing algorithm.
    
    Attributes:
        low_speed_kmh: Speed below which slow rate applies (default: 5 km/h)
        high_speed_kmh: Speed above which fast rate applies (default: 90 km/h)
        slow_rate_sec: Beacon interval when slow/stationary (default: 1800s = 30 min)
        fast_rate_sec: Beacon interval at high speed (default: 120s = 2 min)
        min_turn_angle: Minimum heading change to trigger turn beacon (default: 28°)
        turn_slope: Divisor for speed-based turn threshold (default: 26)
        min_turn_time_sec: Minimum time between turn beacons (default: 15s)
    """
    low_speed_kmh: float = 5.0
    high_speed_kmh: float = 90.0
    slow_rate_sec: float = 1800.0  # 30 minutes
    fast_rate_sec: float = 120.0   # 2 minutes
    min_turn_angle: float = 28.0   # degrees
    turn_slope: float = 26.0
    min_turn_time_sec: float = 15.0


@dataclass
class BeaconState:
    """Internal state tracking for beacon decisions."""
    last_beacon_time: float = 0.0
    last_beacon_lat: Optional[float] = None
    last_beacon_lon: Optional[float] = None
    last_beacon_heading: Optional[float] = None
    last_turn_time: float = 0.0
    point_count: int = 0


class SmartBeacon:
    """Smart beaconing algorithm for GPS track point recording.
    
    Usage:
        beacon = SmartBeacon()
        
        # In your GPS update loop:
        if beacon.should_beacon(lat, lon, speed_kmh, heading):
            # Save the track point to database
            save_track_point(lat, lon, speed_kmh, heading)
    """
    
    def __init__(self, config: Optional[BeaconConfig] = None):
        """Initialize smart beacon with optional custom configuration."""
        self.config = config or BeaconConfig()
        self.state = BeaconState()
    
    def should_beacon(
        self,
        lat: float,
        lon: float,
        speed_kmh: float,
        heading: float,
        current_time: Optional[float] = None
    ) -> bool:
        """Determine if a beacon (track point) should be recorded.
        
        Args:
            lat: Current latitude in decimal degrees
            lon: Current longitude in decimal degrees
            speed_kmh: Current speed in kilometers per hour
            heading: Current heading in degrees (0-360, 0=North)
            current_time: Optional timestamp (defaults to time.time())
            
        Returns:
            True if a track point should be recorded, False otherwise
        """
        if current_time is None:
            current_time = time.time()
        
        # First point is always recorded
        if self.state.last_beacon_time == 0:
            self._record_beacon(lat, lon, heading, current_time)
            return True
        
        time_since_beacon = current_time - self.state.last_beacon_time
        
        # Check for turn beacon
        if self._should_turn_beacon(speed_kmh, heading, current_time):
            self._record_beacon(lat, lon, heading, current_time)
            self.state.last_turn_time = current_time
            return True
        
        # Calculate speed-based beacon interval
        beacon_interval = self._calculate_interval(speed_kmh)
        
        # Time-based beacon
        if time_since_beacon >= beacon_interval:
            self._record_beacon(lat, lon, heading, current_time)
            return True
        
        return False
    
    def _calculate_interval(self, speed_kmh: float) -> float:
        """Calculate beacon interval based on current speed.
        
        Uses linear interpolation between slow_rate and fast_rate
        based on speed between low_speed and high_speed thresholds.
        """
        cfg = self.config
        
        if speed_kmh <= cfg.low_speed_kmh:
            return cfg.slow_rate_sec
        
        if speed_kmh >= cfg.high_speed_kmh:
            return cfg.fast_rate_sec
        
        # Linear interpolation
        speed_range = cfg.high_speed_kmh - cfg.low_speed_kmh
        rate_range = cfg.slow_rate_sec - cfg.fast_rate_sec
        speed_fraction = (speed_kmh - cfg.low_speed_kmh) / speed_range
        
        return cfg.slow_rate_sec - (speed_fraction * rate_range)
    
    def _should_turn_beacon(
        self,
        speed_kmh: float,
        heading: float,
        current_time: float
    ) -> bool:
        """Check if a turn beacon should be triggered.
        
        Turn threshold decreases with speed (more sensitive at higher speeds).
        """
        cfg = self.config
        
        # Need a previous heading to compare
        if self.state.last_beacon_heading is None:
            return False
        
        # Enforce minimum time between turn beacons
        if current_time - self.state.last_turn_time < cfg.min_turn_time_sec:
            return False
        
        # Only check turns when moving
        if speed_kmh < cfg.low_speed_kmh:
            return False
        
        # Calculate heading change (handle 360° wraparound)
        heading_change = abs(self._normalize_heading_diff(
            heading, self.state.last_beacon_heading
        ))
        
        # Turn threshold: min_turn_angle + turn_slope / speed
        # Higher speed = lower threshold = more sensitive to turns
        turn_threshold = cfg.min_turn_angle + (cfg.turn_slope / max(speed_kmh, 1))
        
        return heading_change >= turn_threshold
    
    @staticmethod
    def _normalize_heading_diff(h1: float, h2: float) -> float:
        """Calculate the smallest angle between two headings."""
        diff = h1 - h2
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        return diff
    
    def _record_beacon(
        self,
        lat: float,
        lon: float,
        heading: float,
        current_time: float
    ) -> None:
        """Update internal state after recording a beacon."""
        self.state.last_beacon_time = current_time
        self.state.last_beacon_lat = lat
        self.state.last_beacon_lon = lon
        self.state.last_beacon_heading = heading
        self.state.point_count += 1
    
    def reset(self) -> None:
        """Reset beacon state (e.g., when starting a new track)."""
        self.state = BeaconState()
    
    def get_stats(self) -> dict:
        """Return current beacon statistics."""
        return {
            "point_count": self.state.point_count,
            "last_beacon_time": self.state.last_beacon_time,
            "last_position": (
                self.state.last_beacon_lat,
                self.state.last_beacon_lon
            ) if self.state.last_beacon_lat else None,
            "last_heading": self.state.last_beacon_heading
        }


def calculate_beacon_interval(speed_kmh: float, heading_change: float = 0) -> float:
    """Convenience function for calculating beacon interval.
    
    This is a stateless helper for testing and one-off calculations.
    For actual tracking, use the SmartBeacon class.
    
    Args:
        speed_kmh: Current speed in km/h
        heading_change: Absolute heading change in degrees
        
    Returns:
        Beacon interval in seconds (0 = immediate beacon)
    """
    config = BeaconConfig()
    
    # Immediate beacon on significant turn
    turn_threshold = config.min_turn_angle + (config.turn_slope / max(speed_kmh, 1))
    if heading_change >= turn_threshold and speed_kmh >= config.low_speed_kmh:
        return 0
    
    # Speed-based interval
    if speed_kmh <= config.low_speed_kmh:
        return config.slow_rate_sec
    
    if speed_kmh >= config.high_speed_kmh:
        return config.fast_rate_sec
    
    # Linear interpolation
    speed_range = config.high_speed_kmh - config.low_speed_kmh
    rate_range = config.slow_rate_sec - config.fast_rate_sec
    speed_fraction = (speed_kmh - config.low_speed_kmh) / speed_range
    
    return config.slow_rate_sec - (speed_fraction * rate_range)
