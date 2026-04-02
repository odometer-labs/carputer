#!/bin/bash -e

GPSD_CONFIG="${ROOTFS_DIR}/etc/default/gpsd"

sed -i 's|^DEVICES=.*|DEVICES="/dev/ttyACM0"|' "$GPSD_CONFIG"
sed -i 's|^GPSD_OPTIONS=.*|GPSD_OPTIONS="-F /var/run/gpsd.sock"|' "$GPSD_CONFIG"