
# Wifi Manager

Service providing basic wifi connection management via NetworkManager using its dbus interface.

## Requirements

1. Linux
2. NetworkManager
3. [UV](https://docs.astral.sh/uv/guides/install-python/)

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