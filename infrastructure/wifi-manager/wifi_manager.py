from uuid import uuid4, UUID
from typing import Optional

import sdbus

from sdbus_block.networkmanager import (
    NetworkDeviceGeneric,
    NetworkDeviceWireless,
    NetworkManager,
    NetworkManagerSettings,
    NetworkConnectionSettings,
    AccessPoint,
    WiFiOperationMode,
    ActiveConnection,
    ConnectionType,
    ConnectivityState,
)
from sdbus_block.networkmanager.settings import (
    WirelessSettings,
    WirelessSecuritySettings,
    ConnectionProfile,
    ConnectionSettings,
    Ipv4Settings,
    Ipv6Settings,
    AddressData,
)
from sdbus_block.networkmanager.enums import DeviceType
from sdbus_block.networkmanager.exceptions import (
    NmSettingsInvalidConnectionError,
    NetworkManagerUnknownDeviceError,
    NetworkManagerUnknownConnectionError,
    NmDeviceNotActiveError,
)
from pydantic import BaseModel, SecretStr, Field


# 802.11 standard for WPA personal (psk) requires a passphrase of 8 to 63 ascii characters
PASSWORD_MIN_LENGTH: int = 8
PASSWORD_MAX_LENGTH: int = 63


class WifiManagerBaseException(Exception):
    pass


class WifiDeviceNotFound(WifiManagerBaseException):
    pass


class InvalidConnection(WifiManagerBaseException):
    pass


class InvalidPassword(WifiManagerBaseException):
    pass


class WifiAccessPoint(BaseModel):
    """
    Represents a wifi access point

    :param ssid: broadcast name of wifi network
    :param signal_strength: quality of signal (0-100)
    """
    ssid: str
    signal_strength: int


class StaticNetworkSettings(BaseModel):
    """
    Represents static network configuration settings.
    :param ip: ipv4 address using 255.255.255.255 representation
    :param gateway: gateway ipv4 address, set to None or 0.0.0.0 for no gateway
    :param netmask: number of bits belonging to the network segment of the address, 24 is equivalent to /24 or 255.255.255.0
    """
    ip: str
    gateway: Optional[str]
    netmask: int


class WifiConnectionSettings(BaseModel):
    """
    Represents the mininum number of fields for representing a wifi connection.
    Currently this only supports WPA2 personal for either connecting to an AP or making a hotspot.

    :param hotspot: True if connection object is a hotspot
    :param connection_id: human readable local identifier for this connection (not guaranteed to be unique)
    :param ssid: name of network as seen by nearby devices when looking at available networks to connect to
    :param uuid: unique identifier for this connection object (uuid4)
    :param password: a string between 8-63 ascii characters either for connecting to an existing network or will be the wpa password for the hotspot
    :param static_config: (optional) static network configuration settings, set to none to use dynamic configuration / dhcp
    """
    hotspot: bool
    connection_id: Optional[str]
    ssid: str
    uuid: Optional[UUID] = Field(default_factory=uuid4)
    password: SecretStr = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    static_config: Optional[StaticNetworkSettings] = None

    @staticmethod
    def from_profile(profile: ConnectionProfile) -> "WifiConnectionSettings":
        """
        Convert from internal network manager data structures to the subset used by this application.
        Performs validation of the data structure.
        """

        if not profile.wireless:
            raise InvalidConnection("Missing wireless settings from connection profile")
        if not profile.wireless.ssid:
            raise InvalidConnection("Missing SSID from connection profile")

        if (
            profile.ipv4
            and profile.ipv4.address_data
            and len(profile.ipv4.address_data) > 0
        ):
            address_data = profile.ipv4.address_data[0]
            static_config = StaticNetworkSettings(
                ip=address_data.address,
                netmask=address_data.prefix,
                gateway=profile.ipv4.gateway,
            )
        else:
            static_config = None

        if profile.wireless_security and not profile.wireless_security.psk:
            raise InvalidPassword("Missing wifi security passphrase from settings")

        return WifiConnectionSettings(
            hotspot=True
            if profile.wireless and profile.wireless.mode == "ap"
            else False,
            connection_id=profile.connection.connection_id,
            uuid=UUID(profile.connection.uuid) if profile.connection.uuid else None,
            ssid=profile.wireless.ssid.decode(),
            static_config=static_config,
            password=profile.wireless_security.psk,
        )

    def into_profile(self) -> ConnectionProfile:
        """
        Convert from application specific representation to the internal representation used by network manager
        """
        password = self.password.get_secret_value() if self.password else None
        if self.hotspot:
            ipv4_settings = Ipv4Settings(method="shared")
            if self.static_config:
                ipv4_settings.address_data = [
                    AddressData(self.static_config.ip, self.static_config.netmask)
                ]
                ipv4_settings.gateway = self.static_config.gateway
        else:
            ipv4_settings = (
                Ipv4Settings(
                    method="static",
                    address_data=[
                        AddressData(self.static_config.ip, self.static_config.netmask)
                    ],
                    gateway=self.static_config.gateway,
                )
                if self.static_config
                else Ipv4Settings(method="auto")
            )

        wireless_settings = WirelessSettings(
            ssid=self.ssid.encode(), mode="ap" if self.hotspot else "infrastructure"
        )

        # Not possible to create a hotspot without a password currently
        wireless_security = WirelessSecuritySettings(key_mgmt="wpa-psk", psk=password)

        ipv6_settings = Ipv6Settings(method="disabled")

        connection_uuid = str(self.uuid) if self.uuid else None

        connection_settings = ConnectionSettings(
            connection_type=ConnectionType.WIFI.value,
            uuid=connection_uuid,
            connection_id=self.connection_id,
            autoconnect=not self.hotspot,
        )

        return ConnectionProfile(
            wireless_security=wireless_security,
            wireless=wireless_settings,
            connection=connection_settings,
            ipv4=ipv4_settings,
            ipv6=ipv6_settings,
        )


def setup_system_bus():
    """
    Open a blocking connection to the system bus.

    Underlying message bus daemon supports multiple connections but modifying the same settings
      in parallel via multiple connections can lead to unpredictable behavior.
    """
    sdbus.set_default_bus(sdbus.sd_bus_open_system())


def get_wireless_device_by_interface(interface: str) -> str:
    """Get the device dbus associated with an interface name

    Args:
        interface: network interface name e.g. wlan0
    
    Returns:
        dbus path object corresponding to network interface

    Raises:
        WifiDeviceNotFound if no interface is found with the given name 
        or interface is not a wifi device
    """
    try:
        path = NetworkManager().get_device_by_ip_iface(interface)
    except NetworkManagerUnknownDeviceError:
        raise WifiDeviceNotFound(f"No wifi device found with interface: {interface}")

    device = NetworkDeviceGeneric(path)
    if device.device_type == DeviceType.WIFI:
        return path
    raise WifiDeviceNotFound(f"{interface} is not a valid wifi interface")


def _scan_for_access_points(device: str):
    """Initiate a scan for nearby access points

    Args:
        device: dbus path to wifi device
    """
    NetworkDeviceWireless(device).request_scan({})


def _get_access_point_paths(device: str) -> list[str]:
    """Get dbus object paths associated with access points

    Args:
        device: dbus device path representation

    Returns:
        list of dbus object paths
    :param device: dbus path to wifi device used to get nearby access points
    """
    return NetworkDeviceWireless(device).get_all_access_points()


def get_access_points(interface: str) -> list[WifiAccessPoint]:
    """Scan for and then list the current visible access points, does not show hidden networks..

    Args:
        interface: network interface to check for networks on e.g. wlan0

    Returns:
        list of nearby access point objects
    """
    device = get_wireless_device_by_interface(interface)
    _scan_for_access_points(device)
    ap_paths = _get_access_point_paths(device)
    aps: list[WifiAccessPoint] = []
    for path in ap_paths:
        ap = AccessPoint(path)
        if ap.mode != WiFiOperationMode.INFRASTRUCTURE:
            continue

        aps.append(
            WifiAccessPoint(
                ssid=ap.ssid.decode(), signal_strength=ap.strength
            )
        )
    return aps


def get_available_connections() -> list[str]:
    """Get dbus object paths for current connection profiles

    Returns:
        list of dbus object paths of connection profiles
    """
    return NetworkManagerSettings().connections


def resolve_connection_settings(settings: str) -> ConnectionProfile:
    """Convert dbus profile path into an actual settings object

    Args:
        settings: dbus path object to connection profile

    Returns:
        profile object containing all the settings of that connection
    """
    return NetworkConnectionSettings(settings).get_profile()


def get_wifi_connections() -> list[WifiConnectionSettings]:
    """Get all wifi connections belonging to all interfaces on the device

    Returns:
        list of wifi connection setting objects
    """
    paths = get_available_connections()
    all_connections = [resolve_connection_settings(path) for path in paths]
    wifi_connections = [
        profile
        for profile in all_connections
        if profile.connection.connection_type == ConnectionType.WIFI
    ]
    return [WifiConnectionSettings.from_profile(profile) for profile in wifi_connections]


def get_primary_connection_settings(interface: str) -> Optional[WifiConnectionSettings]:
    """Get the current active connection for the given interface

    Args:
        interface: network interface name e.g. wlan0

    Returns:
        wifi connection settings of active connection or None

    Raises:
        InvalidConnection if security settings are not set
    """
    device = get_wireless_device_by_interface(interface)
    try:
        profile, _ = NetworkDeviceWireless(device).get_applied_connection_profile()
    except NmDeviceNotActiveError:
        return None

    if not profile.wireless_security:
        raise InvalidConnection("Missing wireless security settings")
    profile.wireless_security.psk = "*" * PASSWORD_MIN_LENGTH
    return WifiConnectionSettings.from_profile(profile)


def add_connection(profile: ConnectionProfile) -> str:
    """
    Create a new connection profile and save to disk
    """
    return NetworkManagerSettings().add_connection(profile.to_dbus())


def get_active_connection_path(uuid: str) -> Optional[str]:
    """Get path of active connection object, used to deactivate the current primary connection for an interface.

    Args:
        uuid: id of active connection

    Returns:
        dbus object path of active connection if it exists, None otherwise
    """
    for path in NetworkManager().active_connections:
        connection = ActiveConnection(path)
        if connection.uuid == uuid:
            return path
    return None


def get_saved_connection_path(uuid: str) -> Optional[str]:
    """Get the dbus connection path of a profile with the given uuid

    Args:
        uuid: id of connection profile to search for

    Returns:
        dbus path to connection object if it exists, None otherwise
    """
    paths = get_available_connections()
    for path in paths:
        settings = resolve_connection_settings(path)
        if settings.connection.uuid == uuid:
            return path
    return None


def deactivate_connection(uuid: str | UUID) -> bool:
    """Deactivate an existing connection

    Args:
        uuid: id of existing connection to deactivate
    
    Returns:
        True if connection with given uuid exists, False otherwise
    """
    connection_path = get_active_connection_path(str(uuid))
    if not connection_path:
        return False
    NetworkManager().deactivate_connection(connection_path)
    return True


def activate_connection_path(connection: str, device: str) -> str:
    """Activate a given connection path, return path of new active connection

    Args:
        connection: dbus connection path to activate
        device: dbus device path to activate connection on

    Returns:
        path to new active connection
    """
    return NetworkManager().activate_connection(connection=connection, device=device)


def activate_existing_connection(uuid: str | UUID, interface: str) -> bool:
    """Change the current active connection.

    Args:
        uuid: id of already existing connection profile to activate
        interface: Interface name e.g. wlan0.

    Returns:
        bool: True if connection exists, False otherwise.
    """
    device = get_wireless_device_by_interface(interface)
    connection_path = get_saved_connection_path(str(uuid))
    if not connection_path:
        return False
    activate_connection_path(connection_path, device)
    return True


def add_and_activate_connection(settings: WifiConnectionSettings, interface: str):
    """Create and activate a new connection profile using the given settings

    Args:
        settings: wifi connection settings
        interface: network interface name e.g. wlan0

    Returns:
        None
    """
    device = get_wireless_device_by_interface(interface)
    connection_path = add_connection(settings.into_profile())
    activate_connection_path(connection=connection_path, device=device)


def delete_connection(uuid: UUID | str) -> bool:
    """Delete a connection by its UUID

    Args:
        uuid: id of connection profile to delete

    Returns:
        True if connection exists, False otherwise.
    """
    uuid = str(uuid)
    try:
        NetworkManagerSettings().delete_connection_by_uuid(uuid)
        return True
    except NmSettingsInvalidConnectionError | NetworkManagerUnknownConnectionError:
        return False


def delete_all_wifi_connections():
    """Delete all existing wifi connection profiles.
    """
    connections = get_wifi_connections()
    for connection in connections:
        if connection.uuid:
            delete_connection(connection.uuid)


def connectivity_check(interface: str) -> bool:
    """Check internet connectivity

    Args:
        interface: Interface name e.g. wlan0.

    Returns:
        True if internet is reachable, False otherwise.
    """
    device = get_wireless_device_by_interface(interface)
    return NetworkDeviceWireless(device).ip4_connectivity == ConnectivityState.FULL
