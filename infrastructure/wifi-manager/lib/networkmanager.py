import uuid
from enum import Enum

import sdbus

from sdbus_block.networkmanager import (
    NetworkDeviceGeneric,
    NetworkDeviceWireless,
    NetworkManager,
    NetworkManagerSettings,
    NetworkConnectionSettings,
    NetworkManagerConnectionProperties,
    AccessPoint,
    ConnectionType,
)
from sdbus_block.networkmanager.settings import (
    WirelessSettings,
    WirelessSecuritySettings,
    ConnectionProfile,
    ConnectionSettings,
    Ipv4Settings,
    Ipv6Settings,
)
from sdbus_block.networkmanager.enums import DeviceType


class WifiManagerErrorType(Enum):
    NOT_FOUND = 0
    INVALID_DEVICE = 1
    RESOURCE_EXISTS = 2


class WifiManagerException(Exception):
    def __init__(self, error: WifiManagerErrorType, message: str):
        super().__init__()
        error: WifiManagerErrorType = error
        message: str = message


def setup_system_bus():
    sdbus.set_default_bus(sdbus.sd_bus_open_system())


def get_wifi_device_by_interface(
    interface: str, manager: NetworkManager
) -> NetworkDeviceWireless | None:
    path = manager.get_device_by_ip_iface(interface)
    device = NetworkDeviceGeneric(path)
    return (
        NetworkDeviceWireless(path) if device.device_type == DeviceType.WIFI else None
    )


def get_all_devices() -> list[NetworkDeviceGeneric]:
    devices = NetworkManager().get_all_devices()
    return [NetworkDeviceGeneric(dev) for dev in devices]


def get_wifi_devices() -> list[NetworkDeviceWireless]:
    return [
        NetworkDeviceWireless(dev.path)
        for dev in get_all_devices()
        if dev.device_type == DeviceType.WIFI
    ]


def get_access_points(device: NetworkDeviceWireless) -> list[AccessPoint]:
    device.request_scan()
    return [AccessPoint(ap) for ap in device.get_all_access_points()]


def get_access_point_by_ssid(
    ssid: str, device: NetworkDeviceWireless
) -> AccessPoint | None:
    access_points = get_access_points(device)
    for ap in access_points:
        read_ssid = ap.ssid.decode()
        if read_ssid == ssid:
            return ap
    return None


def _create_wifi_connection(
    interface: str,
    connection_id: str,
    settings: WirelessSettings,
    security: WirelessSecuritySettings,
    ipv4_settings: Ipv4Settings,
    ipv6_settings: Ipv6Settings,
) -> ConnectionProfile:
    connection_settings = ConnectionSettings(
        interface_name=interface,
        connection_type=ConnectionType.WIFI.value,
        uuid=str(uuid.uuid4()),
        connection_id=connection_id,
        autoconnect=True,
    )
    return ConnectionProfile(
        wireless_security=security,
        wireless=settings,
        connection=connection_settings,
        ipv4=ipv4_settings,
        ipv6=ipv6_settings,
    )


def standard_wifi_connection(
    interface: str, connection_id: str, ssid: str, password: str
) -> ConnectionProfile:
    settings = WirelessSettings(ssid=ssid.encode(), mode="infrastructure")
    ipv4_settings = Ipv4Settings(method="auto")
    ipv6_settings = Ipv6Settings(method="auto")
    security = (
        WirelessSecuritySettings(key_mgmt="wpa-psk", auth_alg="open", psk=password)
        if password
        else None
    )
    return _create_wifi_connection(
        interface=interface,
        connection_id=connection_id,
        settings=settings,
        security=security,
        ipv4_settings=ipv4_settings,
        ipv6_settings=ipv6_settings,
    )


def standard_hotspot_connection(
    interface: str, connection_id: str, ssid: str, password: str
) -> ConnectionProfile:
    settings = WirelessSettings(ssid=ssid.encode(), mode="ap")
    ipv4_settings = Ipv4Settings(method="shared")
    ipv6_settings = Ipv6Settings(method="ignore")
    security = WirelessSecuritySettings(key_mgmt="wpa-psk", psk=password)
    return _create_wifi_connection(
        interface=interface,
        connection_id=connection_id,
        settings=settings,
        security=security,
        ipv4_settings=ipv4_settings,
        ipv6_settings=ipv6_settings,
    )


def get_connections():
    connections = NetworkManagerSettings().list_connections()
    return [
        NetworkConnectionSettings(c).get_profile(fetch_secrets=False)
        for c in connections
    ]


def get_wifi_connections(device: NetworkDeviceWireless):
    connections = device.available_connections
    for c in connections:
        settings = NetworkConnectionSettings(c)
        props = settings.get_settings()
        print(props)


def add_connection(profile: ConnectionProfile) -> ConnectionProfile:
    connection_id = profile.connection.connection_id
    settings = NetworkManagerSettings()
    if settings.get_connections_by_id(connection_id):
        raise WifiManagerException(
            WifiManagerErrorType.RESOURCE_EXISTS,
            f"A connection with ID: {connection_id} already exists.",
        )
    connection_path = settings.add_connection(profile.to_dbus())
    return NetworkConnectionSettings(connection_path).get_profile()


def delete_connection(uuid: str):
    NetworkManagerSettings().delete_connection_by_uuid(uuid)
