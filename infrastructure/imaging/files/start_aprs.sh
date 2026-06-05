#!/bin/bash
set -o pipefail
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

# Create log directory
mkdir -p /var/log/carputer/aprs

# Start pipeline
echo "Starting APRS reception on 144.390 MHz..."

# rtl_fm demodulates FM audio, pipes to Direwolf
rtl_fm -f $FREQ -s $SAMPLE_RATE -g 49.6 -p 0 -d $DEVICE - | \
    direwolf -c /opt/aprs/direwolf.conf -r $SAMPLE_RATE -D 1 -