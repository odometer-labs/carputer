#!/bin/bash -e

APP_NAME="carputer"
LOGIN_PASSWORD="$(openssl rand -base64 20)"
PIGEN_REPO="https://github.com/RPI-Distro/pi-gen.git"
PIGEN_BRANCH="arm64"

if [ ! -f ".env" ]; then
    echo "Building an image requires a .env file in this directory."
    echo "See .env.example at the project root for a template."
    exit 1
fi

source .env

if [ -z "$CARPUTER_DEPLOY_KEY" ]; then
    echo "CARPUTER_DEPLOY_KEY must be set in .env to the path of an SSH private key."
    exit 1
fi

if [ ! -f "$CARPUTER_DEPLOY_KEY" ]; then
    echo "SSH key not found at: $CARPUTER_DEPLOY_KEY"
    exit 1
fi

# Stage the deploy key inside the custom stage so it's accessible during the
# build regardless of whether we're running natively or inside Docker.
STAGED_KEY="stage-custom/03-carputer/files/deploy_key"
cp "$CARPUTER_DEPLOY_KEY" "$STAGED_KEY"
chmod 600 "$STAGED_KEY"

cleanup() {
    rm -f "$STAGED_KEY"
}
trap cleanup EXIT

[ -d "./pi-gen" ] && rm -rf pi-gen

git clone --depth 1 --single-branch --branch "$PIGEN_BRANCH" "$PIGEN_REPO"

cp .env stage-custom/03-carputer/files/.env

cp -r stage-custom pi-gen

cd pi-gen

cat > config <<HEREDOC
IMG_NAME="$APP_NAME-img"
TARGET_HOSTNAME="$APP_NAME"
FIRST_USER_NAME="$APP_NAME"
FIRST_USER_PASS="$LOGIN_PASSWORD"

LOCALE_DEFAULT="en_US.UTF-8"
KEYBOARD_KEYMAP="us"
TIMEZONE_DEFAULT="America/Los_Angeles"
ENABLE_CLOUD_INIT=0
ENABLE_SSH=1
STAGE_LIST="stage0 stage1 stage2 stage3 stage-custom"
HEREDOC

if [[ "$(uname)" != "Linux" ]]; then
    echo "Non-Linux host detected — building via Docker (requires Docker Desktop)."
    sudo ./build-docker.sh
else
    sudo ./build.sh
fi

echo ""
echo "Image build complete. Output: ./pi-gen/deploy/"
echo ""
echo "Login credentials"
echo "  User:     $APP_NAME"
echo "  Password: $LOGIN_PASSWORD"
