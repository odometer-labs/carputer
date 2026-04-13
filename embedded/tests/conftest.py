"""Shared fixtures for embedded tests."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EMBEDDED_DIR = REPO_ROOT / "embedded"
INFRA_DIR = REPO_ROOT / "infrastructure"


@pytest.fixture
def chrony_conf_path() -> Path:
    return EMBEDDED_DIR / "ntp_gps_sync" / "chrony.conf"


@pytest.fixture
def chrony_conf(chrony_conf_path: Path) -> str:
    return chrony_conf_path.read_text()


@pytest.fixture
def gpsd_dropin_path() -> Path:
    return EMBEDDED_DIR / "ntp_gps_sync" / "gpsd-depends-chrony.conf"


@pytest.fixture
def gpsd_dropin(gpsd_dropin_path: Path) -> str:
    return gpsd_dropin_path.read_text()


@pytest.fixture
def carputer_service_path() -> Path:
    return INFRA_DIR / "systemd" / "carputer.service"


@pytest.fixture
def carputer_service(carputer_service_path: Path) -> str:
    return carputer_service_path.read_text()
