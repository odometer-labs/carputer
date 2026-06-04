#!/bin/bash -e
# =============================================================================
# Carputer Stage - Local Source Installation (No GitHub)
# =============================================================================
# This script copies local source code into the image instead of cloning
# from GitHub. Used by generate_image_local.sh.
# =============================================================================

echo "Creating carputer application directory"
install -v -m 0755 -o 1000 -g 1000 -d "${ROOTFS_DIR}/opt/carputer"

# Copy staged local source code
echo "Copying local source code to image..."
cp -r files/carputer-source/* "${ROOTFS_DIR}/opt/carputer/"
chown -R 1000:1000 "${ROOTFS_DIR}/opt/carputer"
chmod -R 0755 "${ROOTFS_DIR}/opt/carputer"

# Install environment file
echo "Installing environment configuration..."
install -m 600 "files/.env" "${ROOTFS_DIR}/opt/carputer/.env"
chown 1000:1000 "${ROOTFS_DIR}/opt/carputer/.env"

# Install local docker-compose file (builds from source, no registry pulls)
echo "Installing docker-compose.local.yml..."
install -m 644 "files/docker-compose.local.yml" "${ROOTFS_DIR}/opt/carputer/docker-compose.local.yml"
chown 1000:1000 "${ROOTFS_DIR}/opt/carputer/docker-compose.local.yml"

# Install systemd service (configured for local builds)
echo "Installing carputer systemd service..."
install -m 644 "files/carputer-local.service" "${ROOTFS_DIR}/etc/systemd/system/carputer.service"

# Setup labwc autostart for kiosk mode
echo "Configuring labwc autostart..."
install -v -m 0744 -o 1000 -g 1000 -d "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/.config/labwc"
install -m 644 "files/labwc_autostart" "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/.config/labwc/autostart"
chown -R 1000:1000 "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/.config"

# Configure lightdm autologin
echo "Configuring lightdm autologin..."
install -v -m 0755 -d "${ROOTFS_DIR}/etc/lightdm"
cat > "${ROOTFS_DIR}/etc/lightdm/lightdm.conf" << EOF
[Seat:*]
autologin-user=${FIRST_USER_NAME}
autologin-user-timeout=0
EOF

echo "Local carputer stage complete!"
