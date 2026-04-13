
# Wifi Manager

Service providing basic wifi connection management via NetworkManager using its dbus interface.

Currently this service is limited to WPA2 connections profiles and does not support WEP or WPA3
- this could be added later if desired

## Requirements

1. Debian/RaspbianOS (should work on other distros but hasn't been tested)
2. NetworkManager service installed and running and accessible over dbus
3. Permissions to configure the network such as membership of `netdev`
4. [UV](https://docs.astral.sh/uv/guides/install-python/)

## Usage

TODO expand on this once rest API is implemented

Start the service
`uv run --script main.py`

## Tests

Tests are in the tests directory

Run all tests `uv run pytest tests`
Only unit tests `uv run pytest tests/unit`

### Integration Testing

Integration tests are intended to be run inside a VM with >=2 wifi devices.

This allows test cases to set up a hotspot on one device and connect to it from the other device.

Load the following module to simulate 802-11 radio devices before running tests
`modprobe mac80211_hwsim radios=2`

Example of manually creating a hotspot (this is done automatically in the test cases)
`nmcli device wifi hotspot ssid <SSID> password <PASSWORD> ifname <INTERFACE>`