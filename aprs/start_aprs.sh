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
PPM=0

# Tuner gain in dB. 49.6 is max on many dongles; sweep (28 / 33.8 / 40.2 / 49.6)
# and pick whatever yields the most Direwolf decodes for your antenna.
GAIN=49.6

# Create log directory
mkdir -p /var/log/carputer/aprs

# Start pipeline
echo "Starting APRS reception on 144.390 MHz (ppm=$PPM, gain=$GAIN)..."

# rtl_fm demodulates FM audio, pipes to Direwolf
rtl_fm -f $FREQ -s $SAMPLE_RATE -g $GAIN -p $PPM -d $DEVICE - | \
    direwolf -c /opt/carputer/aprs/direwolf.conf -r $SAMPLE_RATE -D 1 -
