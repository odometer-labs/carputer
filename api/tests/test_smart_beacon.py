"""Tests for smart beaconing algorithm."""

import pytest
from app.beaconing import SmartBeacon, BeaconConfig
from app.beaconing.smart_beacon import calculate_beacon_interval


class TestSmartBeaconing:
    """Tests for smart beaconing algorithm."""
    
    def test_beacon_interval_at_rest(self):
        """At rest, should use slow rate (30 min default)."""
        interval = calculate_beacon_interval(speed_kmh=0, heading_change=0)
        assert interval == 1800  # 30 minutes
    
    def test_beacon_interval_at_highway_speed(self):
        """At highway speed, should use fast rate (2 min default)."""
        interval = calculate_beacon_interval(speed_kmh=120, heading_change=0)
        assert interval == 120  # 2 minutes
    
    def test_beacon_on_turn(self):
        """Should beacon immediately on significant heading change."""
        interval = calculate_beacon_interval(speed_kmh=50, heading_change=45)
        assert interval == 0  # Immediate beacon
    
    @pytest.mark.parametrize("speed,expected_range", [
        (0, (1800, 1800)),      # At rest: slow rate
        (5, (1800, 1800)),      # Low speed threshold: slow rate
        (30, (1200, 1400)),     # Medium speed: interpolated (~1306s)
        (60, (600, 800)),       # Faster: closer to fast rate (~713s)
        (90, (120, 120)),       # High speed threshold: fast rate
        (120, (120, 120)),      # Above threshold: fast rate
    ])
    def test_beacon_interval_speed_scaling(self, speed, expected_range):
        """Beacon interval should scale with speed."""
        interval = calculate_beacon_interval(speed_kmh=speed, heading_change=0)
        assert expected_range[0] <= interval <= expected_range[1]


class TestSmartBeaconClass:
    """Tests for SmartBeacon stateful class."""
    
    def test_first_point_always_beacons(self):
        """First position should always trigger a beacon."""
        beacon = SmartBeacon()
        result = beacon.should_beacon(45.5, -122.6, speed_kmh=0, heading=0)
        assert result is True
    
    def test_immediate_second_point_no_beacon(self):
        """Second point immediately after should not beacon (time-based)."""
        beacon = SmartBeacon()
        t0 = 1000.0
        
        # First point
        beacon.should_beacon(45.5, -122.6, 30, 90, current_time=t0)
        
        # Second point 1 second later, same heading
        result = beacon.should_beacon(45.5001, -122.5999, 30, 90, current_time=t0 + 1)
        assert result is False
    
    def test_turn_triggers_beacon(self):
        """Significant turn should trigger immediate beacon."""
        beacon = SmartBeacon()
        t0 = 1000.0
        
        # First point, heading north
        beacon.should_beacon(45.5, -122.6, 50, 0, current_time=t0)
        
        # Turn 45 degrees at 50 km/h (threshold ~28 + 26/50 = ~28.5°)
        result = beacon.should_beacon(45.5001, -122.5999, 50, 45, current_time=t0 + 20)
        assert result is True
    
    def test_small_turn_no_beacon(self):
        """Small heading change should not trigger beacon."""
        beacon = SmartBeacon()
        t0 = 1000.0
        
        # First point
        beacon.should_beacon(45.5, -122.6, 50, 0, current_time=t0)
        
        # Small turn (10°, below threshold)
        result = beacon.should_beacon(45.5001, -122.5999, 50, 10, current_time=t0 + 20)
        assert result is False
    
    def test_time_based_beacon_at_slow_speed(self):
        """Should beacon after slow_rate when moving slowly."""
        config = BeaconConfig(slow_rate_sec=60)  # 1 minute for faster test
        beacon = SmartBeacon(config)
        t0 = 1000.0
        
        # First point
        beacon.should_beacon(45.5, -122.6, 3, 90, current_time=t0)
        
        # 30 seconds later - should not beacon
        result = beacon.should_beacon(45.5, -122.6, 3, 90, current_time=t0 + 30)
        assert result is False
        
        # 60 seconds later - should beacon
        result = beacon.should_beacon(45.5, -122.6, 3, 90, current_time=t0 + 60)
        assert result is True
    
    def test_time_based_beacon_at_high_speed(self):
        """Should beacon more frequently at high speed."""
        config = BeaconConfig(fast_rate_sec=30)  # 30 sec for test
        beacon = SmartBeacon(config)
        t0 = 1000.0
        
        # First point at high speed
        beacon.should_beacon(45.5, -122.6, 100, 90, current_time=t0)
        
        # 15 seconds later - should not beacon
        result = beacon.should_beacon(45.51, -122.59, 100, 90, current_time=t0 + 15)
        assert result is False
        
        # 30 seconds later - should beacon
        result = beacon.should_beacon(45.52, -122.58, 100, 90, current_time=t0 + 30)
        assert result is True
    
    def test_heading_wraparound_positive(self):
        """Turn detection should handle 360° wraparound (350° -> 10°)."""
        beacon = SmartBeacon()
        t0 = 1000.0
        
        # First point, heading 350°
        beacon.should_beacon(45.5, -122.6, 50, 350, current_time=t0)
        
        # Turn to 30° (40° change, should trigger)
        result = beacon.should_beacon(45.5001, -122.5999, 50, 30, current_time=t0 + 20)
        assert result is True
    
    def test_heading_wraparound_negative(self):
        """Turn detection should handle 360° wraparound (10° -> 350°)."""
        beacon = SmartBeacon()
        t0 = 1000.0
        
        # First point, heading 10°
        beacon.should_beacon(45.5, -122.6, 50, 10, current_time=t0)
        
        # Turn to 330° (40° change, should trigger)
        result = beacon.should_beacon(45.5001, -122.5999, 50, 330, current_time=t0 + 20)
        assert result is True
    
    def test_min_turn_time_enforced(self):
        """Should enforce minimum time between turn beacons."""
        config = BeaconConfig(min_turn_time_sec=30)
        beacon = SmartBeacon(config)
        t0 = 1000.0
        
        # First point
        beacon.should_beacon(45.5, -122.6, 50, 0, current_time=t0)
        
        # First turn at t+20
        beacon.should_beacon(45.5001, -122.5999, 50, 45, current_time=t0 + 20)
        
        # Second turn at t+30 (only 10s after first turn) - should not trigger
        result = beacon.should_beacon(45.5002, -122.5998, 50, 90, current_time=t0 + 30)
        assert result is False
        
        # Third turn at t+55 (35s after first turn) - should trigger
        result = beacon.should_beacon(45.5003, -122.5997, 50, 135, current_time=t0 + 55)
        assert result is True
    
    def test_no_turn_when_stationary(self):
        """Should not trigger turn beacon when speed is below threshold."""
        beacon = SmartBeacon()
        t0 = 1000.0
        
        # First point, stationary
        beacon.should_beacon(45.5, -122.6, 0, 0, current_time=t0)
        
        # "Turn" while stationary (e.g., GPS drift)
        result = beacon.should_beacon(45.5, -122.6, 0, 90, current_time=t0 + 20)
        assert result is False
    
    def test_reset_clears_state(self):
        """Reset should clear all state."""
        beacon = SmartBeacon()
        
        beacon.should_beacon(45.5, -122.6, 50, 90, current_time=1000)
        assert beacon.state.point_count == 1
        
        beacon.reset()
        
        assert beacon.state.point_count == 0
        assert beacon.state.last_beacon_time == 0
        assert beacon.state.last_beacon_heading is None
    
    def test_get_stats(self):
        """Should return current statistics."""
        beacon = SmartBeacon()
        
        beacon.should_beacon(45.5, -122.6, 50, 90, current_time=1000)
        beacon.should_beacon(45.51, -122.59, 50, 90, current_time=2000)
        
        stats = beacon.get_stats()
        
        assert stats["point_count"] == 2
        assert stats["last_beacon_time"] == 2000
        assert stats["last_position"] == (45.51, -122.59)
        assert stats["last_heading"] == 90


class TestCustomConfig:
    """Tests for custom beacon configuration."""
    
    def test_custom_speed_thresholds(self):
        """Custom speed thresholds should be respected."""
        config = BeaconConfig(
            low_speed_kmh=10,
            high_speed_kmh=50,
            slow_rate_sec=600,
            fast_rate_sec=60
        )
        beacon = SmartBeacon(config)
        
        # At 10 km/h (low threshold)
        beacon.state.last_beacon_time = 0
        interval = beacon._calculate_interval(10)
        assert interval == 600
        
        # At 50 km/h (high threshold)
        interval = beacon._calculate_interval(50)
        assert interval == 60
    
    def test_custom_turn_angle(self):
        """Custom turn angle should be respected."""
        config = BeaconConfig(min_turn_angle=45)
        beacon = SmartBeacon(config)
        t0 = 1000.0
        
        beacon.should_beacon(45.5, -122.6, 50, 0, current_time=t0)
        
        # 40° turn should NOT trigger (threshold is 45 + slope/speed)
        result = beacon.should_beacon(45.5001, -122.5999, 50, 40, current_time=t0 + 20)
        assert result is False
        
        # 50° turn SHOULD trigger
        result = beacon.should_beacon(45.5001, -122.5999, 50, 50, current_time=t0 + 25)
        assert result is True
