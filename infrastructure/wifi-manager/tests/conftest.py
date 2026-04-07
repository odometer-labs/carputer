from time import sleep

import pytest
from fastapi.testclient import TestClient

import wifi_manager as wm

from main import app


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
    wm.setup_system_bus()


@pytest.fixture(autouse=True)
def delete_all_connections(pytestconfig, setup_default_bus):
    wm.delete_all_wifi_connections()
    sleep(1)


@pytest.fixture()
def client():
    return TestClient(app)
