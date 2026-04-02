#1/bin/bash -e

APP_NAME="carputer"
PASSWORD="$(openssl rand -base64 20)"
PIGEN_REPO="https://github.com/RPI-Distro/pi-gen.git"
PIGEN_BRANCH="arm64"

[ -d "./pi-gen" ] && rm -rf pi-gen

git clone --depth 1 --single-branch --branch "$PIGEN_BRANCH" "$PIGEN_REPO"

cp -r stage-custom pi-gen

cd pi-gen

cat > config <<HEREDOC
IMG_NAME="$APP_NAME-img"
TARGET_HOSTNAME="$APP_NAME"
FIRST_USER_NAME="$APP_NAME"
FIRST_USER_PASS="$PASSWORD"

LOCALE_DEFAULT="en_US.UTF-8"
KEYBOARD_KEYMAP="us"
TIMEZONE_DEFAULT="America/Los_Angeles"
ENABLE_CLOUD_INIT=0
ENABLE_SSH=1
STAGE_LIST="stage0 stage1 stage2 stage3 stage-custom"
HEREDOC

./build.sh

echo "Built image: deploy/$APP_NAME.img"
echo "Generated login credentials"
echo "User: $APP_NAME"
echo "Default Password: $PASSWORD"
