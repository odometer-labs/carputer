#!/bin/bash -e

DOCKER_INSTALL_URL="https://raw.githubusercontent.com/docker/docker-install/2687d91ddeb3bd6aeae37a90947761efdee87030/install.sh"
SHASUM="93f04ab7de485fb08498d8d0257f11a1ffee145ebcc2074dc21937eacc706a2b  install.sh"

cd /tmp

curl -fsSL "$DOCKER_INSTALL_URL" > install.sh

chmod +x install.sh

echo "$SHASUM" | sha256sum -c

VERSION=29.4.3 ./install.sh

rm install.sh

usermod -aG docker $FIRST_USER_NAME
