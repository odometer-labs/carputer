import lib.networkmanager as nm


TEST_INTERFACE_1 = "wlan0"
TEST_INTERFACE_2 = "wlan1"
TEST_ID = "myid"
TEST_SSID = "foobar"
TEST_PASSWORD = "foobarbaz"
WIFI_TYPE = "802-11-wireless"


def test_create_wifi_profile():
    profile = nm.standard_wifi_connection(
        TEST_INTERFACE_1, TEST_ID, TEST_SSID, TEST_PASSWORD
    )

    connection = profile.connection
    assert connection.connection_id == TEST_ID
    assert connection.connection_type == "802-11-wireless"
    assert connection.autoconnect == True
    assert connection.interface_name == TEST_INTERFACE_1

    ipv4 = profile.ipv4
    assert ipv4.method == "auto"

    wifi_settings = profile.wireless
    assert wifi_settings.ssid == TEST_SSID.encode()

    wifi_security = profile.wireless_security
    assert wifi_security.key_mgmt == "wpa-psk"
    assert wifi_security.psk == TEST_PASSWORD


def test_create_hotspot_profile():
    profile = nm.standard_hotspot_connection(
        TEST_INTERFACE_2, TEST_ID, TEST_SSID, TEST_PASSWORD
    )

    connection = profile.connection
    assert connection.connection_id == TEST_ID
    assert connection.connection_type == "802-11-wireless"
    assert connection.interface_name == TEST_INTERFACE_2

    ipv4 = profile.ipv4
    assert ipv4.method == "shared"

    wifi_settings = profile.wireless
    assert wifi_settings.ssid == TEST_SSID.encode()
    assert wifi_settings.mode == "ap"

    wifi_security = profile.wireless_security
    assert wifi_security.key_mgmt == "wpa-psk"
    assert wifi_security.psk == TEST_PASSWORD
