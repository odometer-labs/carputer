#!/bin/bash
#############################################################
# APRS Reception Pipeline
# RTL-SDR → rtl_fm → Direwolf
#############################################################

# APRS frequency for North America: 144.390 MHz
FREQ=144390000  # Hz

# RTL-SDR device (usually 0)
DEVICE=0

# Sample rate (24000 Hz is good for APRS)
SAMPLE_RATE=24000

# Frequency correction in PPM. Cheap RTL-SDR dongles drift several kHz, which
# on 144.390 MHz is enough to miss nearly all packets. Measure yours with
# `rtl_test -p` (or kalibrate-rtl) and set the result here.
PPM=-3

# Tuner gain in dB. 49.6 is the MAXIMUM on many dongles, but max gain is a
# common cause of "I can't hear local stations": strong APRS transmitters a
# couple of miles away overload the RTL-SDR front-end (intermod / desense) so
# nothing decodes. Measured open-squelch audio level at 49.6 was ~95 (clipping)
# and ~84 at 40.2 - both hot. Start moderate and sweep (20.7 / 25.4 / 33.8 /
# 40.2 / 49.6), watching `direwolf -a 10` audio levels (~50 is ideal) and
# decode counts, then pick the best for your antenna/location.
GAIN=33.8

# Create log directory
mkdir -p /var/log/carputer/aprs

# Reset the RTL-SDR before opening it. If a previous rtl_fm was killed without
# releasing the USB interface (e.g. the pipe was torn down), librtlsdr leaves
# the dongle "claimed" and the next open fails with
#   usb_claim_interface error -6   (LIBUSB_ERROR_BUSY)
# A `systemctl restart` does NOT clear this - it just re-runs the same claim
# against the still-locked interface. Only a USB port reset (electrically the
# same as physically unplugging/replugging) frees it. USBDEVFS_RESET does that
# in software, so the service can self-heal on (re)start and after a reboot.
# Requires rw on the device node; the rtl-sdr udev rule grants that to plugdev,
# and this service runs as Group=plugdev.
reset_sdr() {
    python3 - <<'PY' || true
import fcntl, glob, os
USBDEVFS_RESET = 0x5514  # _IO('U', 20)
for d in glob.glob('/sys/bus/usb/devices/*'):
    try:
        if open(d + '/idVendor').read().strip() != '0bda':
            continue
        if open(d + '/idProduct').read().strip() != '2838':
            continue
        bus = int(open(d + '/busnum').read())
        dev = int(open(d + '/devnum').read())
        node = '/dev/bus/usb/%03d/%03d' % (bus, dev)
        fd = os.open(node, os.O_WRONLY)
        try:
            fcntl.ioctl(fd, USBDEVFS_RESET, 0)
            print('reset RTL-SDR at', node)
        finally:
            os.close(fd)
    except Exception as e:
        print('reset_sdr: skipping', d, '->', e)
PY
}

echo "Resetting RTL-SDR (USBDEVFS_RESET) before start..."
reset_sdr
# Give the kernel a moment to re-enumerate the dongle after the reset.
sleep 2

# Start pipeline
echo "Starting APRS reception on 144.390 MHz (ppm=$PPM, gain=$GAIN)..."

# rtl_fm demodulates FM audio, pipes to Direwolf
rtl_fm -f $FREQ -s $SAMPLE_RATE -g $GAIN -p $PPM -d $DEVICE - | \
    direwolf -c /opt/carputer/aprs/direwolf.conf -r $SAMPLE_RATE -D 1 -
