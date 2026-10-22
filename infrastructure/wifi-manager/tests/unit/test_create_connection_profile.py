import wifi_manager as nm

import pytest

TEST_INTERFACE_1 = "wlan0"
TEST_INTERFACE_2 = "wlan1"
TEST_ID = "myid"
TEST_SSID = "foobar"
TEST_PASSWORD = "foobarbaz"
WIFI_TYPE = "802-11-wireless"


@pytest.mark.parametrize(
    "config",
    [
        {
            "hotspot": False,
            "static": False,
            "ssid": "abc",
            "connection_id": "abc_connection",
            "password": "password123",
            "ip": None,
            "gateway": None,
            "netmask": None,
        },
        {
            "hotspot": False,
            "static": True,
            "ssid": "abc",
            "connection_id": "abc_connection",
            "password": "password123",
            "ip": "192.168.1.5",
            "gateway": "0.0.0.0",
            "netmask": 24,
        },
        {
            "hotspot": True,
            "static": False,
            "interface": "wlan1",
            "ssid": "foo",
            "connection_id": "foo_connection",
            "password": TEST_PASSWORD,
            "ip": None,
            "gateway": None,
            "netmask": None,
        },
        {
            "hotspot": False,
            "static": True,
            "ssid": "foo",
            "connection_id": "foo_connection",
            "password": TEST_PASSWORD,
            "ip": "101.1.22.33",
            "gateway": "0.0.0.0",
            "netmask": 24,
        },
    ],
)
def test_create_connection(config):
    if config["static"]:
        static_config = nm.StaticNetworkSettings(
            ip=config["ip"], gateway=config["gateway"], netmask=config["netmask"]
        )
    else:
        static_config = None

    settings = nm.WifiConnectionSettings(
        hotspot=config["hotspot"],
        connection_id=config["connection_id"],
        ssid=config["ssid"],
        password=config["password"],
        static_config=static_config,
    )

    profile = settings.into_profile()

    connection = profile.connection
    assert connection.connection_id == config["connection_id"]
    assert connection.connection_type == "802-11-wireless"
    assert connection.uuid != None
    assert connection.autoconnect == (not config["hotspot"])

    ipv4 = profile.ipv4
    assert ipv4

    if config["hotspot"]:
        expected_method = "shared"
    elif config["static"]:
        expected_method = "static"
    else:
        expected_method = "auto"

    assert ipv4.method == expected_method

    if expected_method == "static":
        assert ipv4.address_data
        assert len(ipv4.address_data) == 1
        address_data = ipv4.address_data[0]
        assert address_data.address == config["ip"]
        assert address_data.prefix == config["netmask"]
        assert ipv4.gateway == config["gateway"]

    ipv6 = profile.ipv6
    assert ipv6
    assert ipv6.method == "disabled"

    wifi_settings = profile.wireless
    assert wifi_settings
    assert wifi_settings.ssid == config["ssid"].encode()

    wifi_security = profile.wireless_security
    assert wifi_security
    assert wifi_security.key_mgmt == "wpa-psk"
    assert wifi_security.psk == config["password"]

    settings = nm.WifiConnectionSettings.from_profile(profile)
    assert settings.hotspot == config["hotspot"]
    assert settings.connection_id == config["connection_id"]
    assert settings.ssid == config["ssid"]
    if settings.password:
        assert settings.password.get_secret_value() == config["password"]
    else:
        assert settings.password == config["password"]
    assert settings.static_config == static_config
