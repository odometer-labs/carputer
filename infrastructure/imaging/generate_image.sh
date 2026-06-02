#!/bin/bash -e

APP_NAME="carputer"
LOGIN_PASSWORD="$(openssl rand -base64 20)"
PIGEN_REPO="https://github.com/RPI-Distro/pi-gen.git"
PIGEN_BRANCH="arm64"

if [ ! -f ".env" ]
then
	echo "Building an imagine requires creating a .env and copying it to this directory"
	echo "See the .env.example at the root of this project for a template env file"
	exit 1
fi

[ -d "./pi-gen" ] && rm -rf pi-gen

git clone --depth 1 --single-branch --branch "$PIGEN_BRANCH" "$PIGEN_REPO"

cp .env files

cp setup_script.sh stage-custom/01-carputer/01-run-chroot.sh

chmod +x stage-custom/01-carputer/01-run-chroot.sh

cp -r files stage-custom/01-carputer

cp -r stage-custom pi-gen

cd pi-gen

rm stage2/EXPORT_IMAGE

cat > config << EOF
IMG_NAME="$APP_NAME-img"
TARGET_HOSTNAME="$APP_NAME"
FIRST_USER_NAME="$APP_NAME"
FIRST_USER_PASS="$LOGIN_PASSWORD"

DISABLE_FIRST_BOOT_USER_RENAME=1

WPA_COUNTRY=US

LOCALE_DEFAULT="en_US.UTF-8"
KEYBOARD_KEYMAP="us"
TIMEZONE_DEFAULT="America/Los_Angeles"
ENABLE_CLOUD_INIT=0
ENABLE_SSH=1
STAGE_LIST="stage0 stage1 stage2 stage3 stage-custom"
EOF

sudo ./build.sh

echo "Generated login credentials"
echo "User: $APP_NAME"
echo "Default Password: $LOGIN_PASSWORD"
