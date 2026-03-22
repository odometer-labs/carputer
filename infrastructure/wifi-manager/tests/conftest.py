import pytest

import lib.networkmanager as nm


def pytest_addoption(parser):
    parser.addoption(
        "--interface_1",
        action="store",
        default="wlan0",
        help="Name of wifi interface 1",
    )
    parser.addoption(
        "--interface_2",
        action="store",
        default="wlan1",
        help="Name of wifi interface 2",
    )


@pytest.fixture(scope="session", autouse=True)
def setup_default_bus():
    nm.setup_system_bus()


@pytest.fixture()
def device(pytestconfig):
    interface = pytestconfig.getoption("--interface")
    device = nm.get_wifi_device_by_interface(interface)
    if not device:
        pytest.exit(
            f"Unable to find device associated with supplied interface: {interface}"
        )
    return device
