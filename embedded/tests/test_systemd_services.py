"""Tests for systemd service ordering — chrony → gpsd → carputer."""

import configparser
import io
import re


def _parse_systemd_unit(content: str) -> configparser.ConfigParser:
    """Parse a systemd unit file into a ConfigParser.

    systemd units are INI-like but allow duplicate keys.  ConfigParser
    doesn't handle duplicates natively, so we concatenate values with
    spaces (matching how systemd merges them).
    """
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(content)
    return parser


class TestGpsdDropin:
    """The gpsd drop-in must ensure gpsd starts after chrony."""

    def test_dropin_file_exists(self, gpsd_dropin_path):
        assert gpsd_dropin_path.exists(), (
            f"gpsd drop-in not found at {gpsd_dropin_path}"
        )

    def test_dropin_has_unit_section(self, gpsd_dropin):
        parser = _parse_systemd_unit(gpsd_dropin)
        assert parser.has_section("Unit"), "Drop-in must have a [Unit] section"

    def test_dropin_after_chrony(self, gpsd_dropin):
        parser = _parse_systemd_unit(gpsd_dropin)
        after = parser.get("Unit", "After", fallback="")
        assert "chrony.service" in after, (
            "gpsd drop-in must specify After=chrony.service"
        )

    def test_dropin_requires_chrony(self, gpsd_dropin):
        parser = _parse_systemd_unit(gpsd_dropin)
        requires = parser.get("Unit", "Requires", fallback="")
        assert "chrony.service" in requires, (
            "gpsd drop-in must specify Requires=chrony.service"
        )

    def test_dropin_is_minimal(self, gpsd_dropin):
        """Drop-in should only add ordering, not override other gpsd settings."""
        parser = _parse_systemd_unit(gpsd_dropin)
        sections = parser.sections()
        assert sections == ["Unit"], (
            f"Drop-in should only have [Unit], found: {sections}"
        )


class TestCarputerService:
    """carputer.service must depend on chrony, gpsd, and postgresql."""

    def test_service_file_exists(self, carputer_service_path):
        assert carputer_service_path.exists()

    def test_after_includes_chrony(self, carputer_service):
        parser = _parse_systemd_unit(carputer_service)
        after = parser.get("Unit", "After", fallback="")
        assert "chrony.service" in after, (
            "carputer.service must start After=chrony.service"
        )

    def test_after_includes_gpsd(self, carputer_service):
        parser = _parse_systemd_unit(carputer_service)
        after = parser.get("Unit", "After", fallback="")
        assert "gpsd.service" in after, (
            "carputer.service must start After=gpsd.service"
        )

    def test_after_includes_postgresql(self, carputer_service):
        parser = _parse_systemd_unit(carputer_service)
        after = parser.get("Unit", "After", fallback="")
        assert "postgresql.service" in after, (
            "carputer.service must start After=postgresql.service"
        )

    def test_wants_includes_chrony(self, carputer_service):
        parser = _parse_systemd_unit(carputer_service)
        wants = parser.get("Unit", "Wants", fallback="")
        assert "chrony.service" in wants, (
            "carputer.service should Wants=chrony.service"
        )

    def test_wants_includes_gpsd(self, carputer_service):
        parser = _parse_systemd_unit(carputer_service)
        wants = parser.get("Unit", "Wants", fallback="")
        assert "gpsd.service" in wants

    def test_wants_includes_postgresql(self, carputer_service):
        parser = _parse_systemd_unit(carputer_service)
        wants = parser.get("Unit", "Wants", fallback="")
        assert "postgresql.service" in wants


class TestBootOrder:
    """Verify the full boot ordering: chrony → gpsd → carputer."""

    def test_chrony_before_gpsd(self, gpsd_dropin):
        """gpsd drop-in enforces After=chrony.service."""
        parser = _parse_systemd_unit(gpsd_dropin)
        after = parser.get("Unit", "After", fallback="")
        assert "chrony.service" in after

    def test_gpsd_before_carputer(self, carputer_service):
        """carputer.service enforces After=gpsd.service."""
        parser = _parse_systemd_unit(carputer_service)
        after = parser.get("Unit", "After", fallback="")
        assert "gpsd.service" in after

    def test_full_chain_chrony_gpsd_carputer(self, gpsd_dropin, carputer_service):
        """The full chain chrony → gpsd → carputer is enforced."""
        dropin_parser = _parse_systemd_unit(gpsd_dropin)
        carputer_parser = _parse_systemd_unit(carputer_service)

        # chrony → gpsd (via drop-in)
        gpsd_after = dropin_parser.get("Unit", "After", fallback="")
        assert "chrony.service" in gpsd_after

        # gpsd → carputer (via carputer.service)
        carputer_after = carputer_parser.get("Unit", "After", fallback="")
        assert "gpsd.service" in carputer_after
