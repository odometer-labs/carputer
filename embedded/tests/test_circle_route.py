"""Tests for circular route generation around Portland State University."""

import math

import pytest

from gpsd_mock.circle_route import CircleRoute

PSU_LAT = 45.5104
PSU_LON = -122.68365
RADIUS_MI = 0.5
# 0.5 mi ≈ 804.672 m
RADIUS_M = RADIUS_MI * 1609.344


class TestCircleRouteInit:
    def test_center_coordinates(self):
        route = CircleRoute(center_lat=PSU_LAT, center_lon=PSU_LON, radius_mi=RADIUS_MI)
        assert route.center_lat == PSU_LAT
        assert route.center_lon == PSU_LON

    def test_radius_stored_in_meters(self):
        route = CircleRoute(center_lat=PSU_LAT, center_lon=PSU_LON, radius_mi=RADIUS_MI)
        assert math.isclose(route.radius_m, RADIUS_M, rel_tol=1e-6)

    def test_default_speed_is_reasonable(self):
        """Default speed should be a slow walk/drive, e.g. ~5 m/s (~11 mph)."""
        route = CircleRoute(center_lat=PSU_LAT, center_lon=PSU_LON, radius_mi=RADIUS_MI)
        assert 1.0 <= route.speed_mps <= 15.0


class TestCircleRoutePosition:
    @pytest.fixture
    def route(self):
        return CircleRoute(center_lat=PSU_LAT, center_lon=PSU_LON, radius_mi=RADIUS_MI)

    def test_position_at_t0_is_on_circle(self, route):
        """At t=0 the point should be ~radius_m from center."""
        pos = route.position_at(0.0)
        dist = _haversine_m(PSU_LAT, PSU_LON, pos["lat"], pos["lon"])
        assert math.isclose(dist, RADIUS_M, rel_tol=0.02)

    def test_position_at_quarter_period(self, route):
        """At t=period/4 should be ~radius_m from center and ~90° from start."""
        period = route.period_seconds
        pos = route.position_at(period / 4)
        dist = _haversine_m(PSU_LAT, PSU_LON, pos["lat"], pos["lon"])
        assert math.isclose(dist, RADIUS_M, rel_tol=0.02)

    def test_position_at_full_period_returns_to_start(self, route):
        """After one full period, should return near starting point."""
        period = route.period_seconds
        pos0 = route.position_at(0.0)
        pos1 = route.position_at(period)
        assert math.isclose(pos0["lat"], pos1["lat"], abs_tol=1e-6)
        assert math.isclose(pos0["lon"], pos1["lon"], abs_tol=1e-6)

    def test_position_dict_has_required_keys(self, route):
        pos = route.position_at(0.0)
        assert "lat" in pos
        assert "lon" in pos
        assert "speed" in pos
        assert "heading" in pos

    def test_speed_is_constant(self, route):
        """Speed should be roughly constant around the circle."""
        for t in [0, 10, 50, 100]:
            pos = route.position_at(float(t))
            assert math.isclose(pos["speed"], route.speed_mps, rel_tol=0.01)

    def test_heading_changes_over_time(self, route):
        """Heading should differ at different times (we're going in a circle)."""
        h0 = route.position_at(0.0)["heading"]
        h1 = route.position_at(route.period_seconds / 4)["heading"]
        assert not math.isclose(h0, h1, abs_tol=1.0)

    def test_heading_is_0_to_360(self, route):
        for t in [0, 30, 60, 120, 200]:
            h = route.position_at(float(t))["heading"]
            assert 0.0 <= h < 360.0


def _haversine_m(lat1, lon1, lat2, lon2):
    """Haversine distance in meters between two WGS84 points."""
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
