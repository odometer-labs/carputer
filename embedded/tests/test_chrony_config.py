"""Tests for chrony.conf — GPS time discipline via GPSD shared memory."""

import re


class TestChronyConfExists:
    def test_file_exists(self, chrony_conf_path):
        assert chrony_conf_path.exists(), f"chrony.conf not found at {chrony_conf_path}"


class TestSHMRefclocks:
    """GPSD writes time to SHM segments 0 (NMEA) and 1 (PPS).
    chrony must be configured to read both."""

    def test_shm0_nmea_refclock_present(self, chrony_conf):
        assert re.search(r"^refclock\s+SHM\s+0\b", chrony_conf, re.MULTILINE), (
            "Missing SHM 0 (NMEA) refclock"
        )

    def test_shm0_has_refid_nmea(self, chrony_conf):
        match = re.search(r"^refclock\s+SHM\s+0\b.*", chrony_conf, re.MULTILINE)
        assert match and "refid NMEA" in match.group(), (
            "SHM 0 refclock should have refid NMEA"
        )

    def test_shm0_is_noselect(self, chrony_conf):
        """NMEA alone is too coarse — it must be noselect (paired with PPS)."""
        match = re.search(r"^refclock\s+SHM\s+0\b.*", chrony_conf, re.MULTILINE)
        assert match and "noselect" in match.group(), (
            "SHM 0 (NMEA) should be noselect — too coarse to select alone"
        )

    def test_shm1_pps_refclock_present(self, chrony_conf):
        assert re.search(r"^refclock\s+SHM\s+1\b", chrony_conf, re.MULTILINE), (
            "Missing SHM 1 (PPS) refclock"
        )

    def test_shm1_has_refid_pps(self, chrony_conf):
        match = re.search(r"^refclock\s+SHM\s+1\b.*", chrony_conf, re.MULTILINE)
        assert match and "refid PPS" in match.group(), (
            "SHM 1 refclock should have refid PPS"
        )

    def test_shm1_is_preferred(self, chrony_conf):
        """PPS is the most accurate source and should be preferred."""
        match = re.search(r"^refclock\s+SHM\s+1\b.*", chrony_conf, re.MULTILINE)
        assert match and "prefer" in match.group(), (
            "SHM 1 (PPS) should be the preferred time source"
        )

    def test_shm1_locked_to_nmea(self, chrony_conf):
        """PPS provides edge-only timing; it needs NMEA for absolute time."""
        match = re.search(r"^refclock\s+SHM\s+1\b.*", chrony_conf, re.MULTILINE)
        assert match and "lock NMEA" in match.group(), (
            "SHM 1 (PPS) should lock to NMEA for absolute time reference"
        )


class TestNTPFallback:
    """When there's no GPS fix (e.g. cold boot indoors), NTP pools provide
    a fallback time source."""

    def test_has_ntp_pool(self, chrony_conf):
        assert re.search(r"^pool\s+\S+.*iburst", chrony_conf, re.MULTILINE), (
            "Should have at least one NTP pool with iburst"
        )


class TestBootTimestep:
    def test_makestep_configured(self, chrony_conf):
        """Allow a large initial clock step on boot to handle cold-start drift."""
        assert re.search(r"^makestep\s+", chrony_conf, re.MULTILINE), (
            "makestep must be configured for boot-time clock correction"
        )


class TestDriftfile:
    def test_driftfile_configured(self, chrony_conf):
        assert re.search(r"^driftfile\s+/var/lib/chrony/chrony\.drift", chrony_conf, re.MULTILINE), (
            "driftfile should be /var/lib/chrony/chrony.drift"
        )


class TestAccessControl:
    def test_binds_localhost_only(self, chrony_conf):
        """chronyc command access should be restricted to localhost."""
        assert "bindcmdaddress 127.0.0.1" in chrony_conf
        assert "bindcmdaddress ::1" in chrony_conf
