"""Tests for gpsd TPV message factory."""

from datetime import datetime, timezone

import pytest

from gpsd_mock.tpv_factory import make_tpv


class TestMakeTPV:
    def test_class_is_tpv(self):
        tpv = make_tpv(lat=45.5104, lon=-122.68365, speed=5.0, heading=90.0)
        assert tpv["class"] == "TPV"

    def test_mode_is_3d(self):
        tpv = make_tpv(lat=45.5104, lon=-122.68365, speed=5.0, heading=90.0)
        assert tpv["mode"] == 3

    def test_coordinates(self):
        tpv = make_tpv(lat=45.5104, lon=-122.68365, speed=5.0, heading=90.0)
        assert tpv["lat"] == 45.5104
        assert tpv["lon"] == -122.68365

    def test_speed_in_mps(self):
        tpv = make_tpv(lat=45.5104, lon=-122.68365, speed=5.0, heading=90.0)
        assert tpv["speed"] == 5.0

    def test_heading_as_track(self):
        """gpsd uses 'track' for heading."""
        tpv = make_tpv(lat=45.5104, lon=-122.68365, speed=5.0, heading=270.5)
        assert tpv["track"] == 270.5

    def test_device_field(self):
        tpv = make_tpv(lat=45.5104, lon=-122.68365, speed=5.0, heading=90.0)
        assert tpv["device"] == "/dev/ttyACM0"

    def test_time_is_iso8601_utc(self):
        tpv = make_tpv(lat=45.5104, lon=-122.68365, speed=5.0, heading=90.0)
        ts = tpv["time"]
        # Should parse as valid ISO 8601 and be in UTC
        dt = datetime.fromisoformat(ts)
        assert dt.tzinfo is not None

    def test_custom_time(self):
        t = datetime(2026, 4, 9, 12, 0, 0, tzinfo=timezone.utc)
        tpv = make_tpv(lat=45.5, lon=-122.6, speed=1.0, heading=0.0, time=t)
        assert tpv["time"] == "2026-04-09T12:00:00+00:00"

    def test_has_altitude(self):
        tpv = make_tpv(lat=45.5104, lon=-122.68365, speed=5.0, heading=90.0)
        assert "altHAE" in tpv
        assert isinstance(tpv["altHAE"], float)

    def test_no_null_values(self):
        """gpsd never sends null — all present fields must have values."""
        tpv = make_tpv(lat=45.5104, lon=-122.68365, speed=5.0, heading=90.0)
        for key, val in tpv.items():
            assert val is not None, f"Field '{key}' is None"
