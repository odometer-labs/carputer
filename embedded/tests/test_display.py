"""Tests for the gpsd intake display helpers."""

import pytest

from gpsd_mock.display import _bearing_to_compass, _format_tpv


class TestBearingToCompass:
    @pytest.mark.parametrize("deg, expected", [
        (0.0, "N"),
        (90.0, "E"),
        (180.0, "S"),
        (270.0, "W"),
        (45.0, "NE"),
        (135.0, "SE"),
        (225.0, "SW"),
        (315.0, "NW"),
        (359.9, "N"),
    ])
    def test_cardinal_and_ordinal(self, deg, expected):
        assert _bearing_to_compass(deg) == expected


class TestFormatTPV:
    def test_contains_coordinates(self):
        tpv = {"lat": 45.5104, "lon": -122.68365, "speed": 5.0, "track": 90.0,
               "altHAE": 15.0, "time": "2026-04-09T12:00:00+00:00"}
        line = _format_tpv(tpv)
        assert "45.510400" in line
        assert "-122.683650" in line

    def test_speed_converted_to_mph(self):
        tpv = {"lat": 0.0, "lon": 0.0, "speed": 5.0, "track": 0.0,
               "altHAE": 0.0, "time": ""}
        line = _format_tpv(tpv)
        # 5 m/s * 2.237 ≈ 11.2 mph
        assert "11.2" in line

    def test_heading_compass_shown(self):
        tpv = {"lat": 0.0, "lon": 0.0, "speed": 0.0, "track": 270.0,
               "altHAE": 0.0, "time": ""}
        line = _format_tpv(tpv)
        assert "W" in line

    def test_handles_missing_fields(self):
        tpv = {"class": "TPV"}
        line = _format_tpv(tpv)
        assert "0.000000" in line
