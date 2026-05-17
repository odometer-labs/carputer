#!/bin/bash -e

CARPUTER_REPO="git@github.com:odometer-labs/carputer.git"

source "files/.env"

echo "Creating SSH config containg deployment key"
install -v -m 0700 -o 1000 -g 1000 -d "${ROOTFS_DIR}"/home/"${FIRST_USER_NAME}"/.ssh
cp "${CARPUTER_DEPLOY_KEY}" "${ROOTFS_DIR}"/home/"${FIRST_USER_NAME}"/.ssh/id_ed25519
# cp "${CARPUTER_DEPLOY_KEY}.pub" "${ROOTFS_DIR}"/home/"${FIRST_USER_NAME}"/.ssh/id_ed25519.pub
ssh-keyscan github.com > "${ROOTFS_DIR}"/home/"${FIRST_USER_NAME}"/.ssh/known_hosts
chown -R 1000:1000 "${ROOTFS_DIR}"/home/"${FIRST_USER_NAME}"/.ssh/
chmod 0600 "${ROOTFS_DIR}"/home/"${FIRST_USER_NAME}"/.ssh/*

echo "Creating carputer application directory"
install -v -m 0700 -o 1000 -g 1000 -d "${ROOTFS_DIR}/opt/carputer"
GIT_SSH_COMMAND="ssh -i ${CARPUTER_DEPLOY_KEY}" git clone --depth 1 --single-branch "$CARPUTER_REPO" "${ROOTFS_DIR}/opt/carputer"
chown -R 1000:1000 "${ROOTFS_DIR}/opt/carputer"
chmod -R 0600 "${ROOTFS_DIR}/opt/carputer"

install -m 600 "files/.env" "$ROOTFS_DIR/opt/${FIRST_USER_NAME}"
install -m 600 "files/carputer.service" "$ROOTFS_DIR/etc/systemd/system"
