from time import sleep

import pytest

import wifi_manager as nm

HOTSPOT_ID = "myhotspot"
CONNECTION_ID = "myconnection"
SSID = "examplessid"
PASSWORD = "supersecret"


def test_create_and_delete_connection(pytestconfig):
    if1 = pytestconfig.getoption("--interface_1")
    if2 = pytestconfig.getoption("--interface_2")

    hotspot_connection = nm.WifiConnectionSettings(
        hotspot=True,
        connection_id=HOTSPOT_ID,
        ssid=SSID,
        password=PASSWORD,
        static_config=None,
    )
    ap_connection = nm.WifiConnectionSettings(
        hotspot=False,
        connection_id=CONNECTION_ID,
        ssid=SSID,
        password=PASSWORD,
        static_config=None,
    )

    nm.add_and_activate_connection(settings=hotspot_connection, interface=if1)
    nm.add_and_activate_connection(settings=ap_connection, interface=if2)

    sleep(1)  # Connection can take a second to activate

    d1_connection = nm.get_primary_connection_settings(if1)
    d2_connection = nm.get_primary_connection_settings(if2)

    assert d1_connection.connection_id == HOTSPOT_ID
    assert d2_connection.connection_id == CONNECTION_ID

    # Attempting to create duplicate connections should fail
    with pytest.raises(Exception):
        nm.add_connection(hotspot_connection.into_profile())

    with pytest.raises(Exception):
        nm.add_connection(ap_connection.into_profile())

    assert nm.delete_connection(str(d1_connection.uuid)) == True
    assert nm.delete_connection(str(d2_connection.uuid)) == True

    # Deleting a non-existent connection should fail
    assert nm.delete_connection(str(d1_connection.uuid)) == False
    assert nm.delete_connection(str(d2_connection.uuid)) == False


def test_created_hotspot_is_visible_as_access_point(pytestconfig):
    interface = pytestconfig.getoption("--interface_2")

    settings = nm.WifiConnectionSettings(
        hotspot=True,
        connection_id=CONNECTION_ID,
        ssid=SSID,
        password=PASSWORD,
        static_config=None,
    )

    nm.add_and_activate_connection(settings=settings, interface=interface)

    sleep(3)  # Connection can take some time to activate

    connection = nm.get_primary_connection_settings(interface)
    assert connection.connection_id == CONNECTION_ID

    access_points = nm.get_access_points(interface)
    assert len(access_points) == 1, (
        "Created hotspot should be visible as an access point"
    )
    hotspot_ap = access_points[0]
    assert hotspot_ap.ssid == SSID
    assert hotspot_ap.security == "wpa-psk"

    assert connection.uuid
    nm.delete_connection(connection.uuid)
