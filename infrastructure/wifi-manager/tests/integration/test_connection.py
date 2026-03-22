from time import sleep

import pytest

import lib.networkmanager as nm

HOTSPOT_ID = "myhotspot"
CONNECTION_ID = "myconnection"
SSID = "examplessid"
PASSWORD = "supersecret"


def test_create_hotspot_and_connect_to_it(pytestconfig):
    if1 = pytestconfig.getoption("--interface_1")
    if2 = pytestconfig.getoption("--interface_2")

    hotspot = nm.standard_hotspot_connection(if1, HOTSPOT_ID, SSID, PASSWORD)
    connection = nm.standard_wifi_connection(if2, CONNECTION_ID, SSID, PASSWORD)

    created_hotspot = nm.add_connection(hotspot)
    sleep(1)
    created_connection = nm.add_connection(connection)

    # Attempting to create duplicate connections should fail
    with pytest.raises(Exception):
        nm.add_connection(hotspot)

    with pytest.raises(Exception):
        nm.add_connection(connection)

    nm.delete_connection(created_connection.connection.uuid)
    nm.delete_connection(created_hotspot.connection.uuid)

    # Deleting a non-existent connection should fail
    with pytest.raises(Exception):
        nm.delete_connection(created_connection.connection.uuid)
        nm.delete_connection(created_hotspot.connection.uuid)

    with pytest.raises(Exception):
        nm.delete_connection(created_hotspot.connection.uuid)
