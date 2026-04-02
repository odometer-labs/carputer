#!/bin/bash -e

CARPUTER_DST="${ROOTFS_DIR}/opt/carputer"
SERVICE_DST="${ROOTFS_DIR}/etc/systemd/system"

install -m 644 files/docker-compose.yml "$CARPUTER_DST"
install -m 644 files/carputer.service "$SERVICE_DST"