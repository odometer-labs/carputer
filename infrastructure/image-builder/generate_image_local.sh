#!/bin/bash -e
# =============================================================================
# Carputer Image Builder - Local Source (No GitHub)
# =============================================================================
# Builds a Raspbian arm64 image with the carputer stack from LOCAL source code.
# Does NOT clone from GitHub - copies your local working directory instead.
#
# Usage:
#   cd infrastructure/image-builder
#   ./generate_image_local.sh
# =============================================================================

APP_NAME="carputer"
LOGIN_PASSWORD="$(openssl rand -base64 20)"
PIGEN_REPO="https://github.com/RPI-Distro/pi-gen.git"
PIGEN_BRANCH="arm64"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=========================================="
echo "Carputer Local Image Builder"
echo "=========================================="
echo "Project root: $PROJECT_ROOT"
echo ""

# Check for .env file
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "Building an image requires a .env file in this directory."
    echo "See .env.example at the project root for a template."
    echo ""
    echo "Minimum required variables:"
    echo "  POSTGRES_USER=carputer"
    echo "  POSTGRES_PASSWORD=<your-password>"
    echo "  POSTGRES_DB=carputer"
    exit 1
fi

source "$SCRIPT_DIR/.env"

# Validate required environment variables
REQUIRED_VARS=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var must be set in .env"
        exit 1
    fi
done

# Create staging directory for local source
STAGED_SOURCE="$SCRIPT_DIR/stage-custom/03-carputer/files/carputer-source"
echo "Staging local source code..."

# Clean previous staged source
rm -rf "$STAGED_SOURCE"
mkdir -p "$STAGED_SOURCE"

# Copy relevant directories (excluding build artifacts, venvs, etc.)
rsync -a --progress \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='node_modules' \
    --exclude='dist' \
    --exclude='build' \
    --exclude='.eggs' \
    --exclude='*.egg-info' \
    --exclude='.mypy_cache' \
    --exclude='.ruff_cache' \
    --exclude='pi-gen' \
    --exclude='.env' \
    --exclude='*.img' \
    --exclude='*.zip' \
    "$PROJECT_ROOT/" "$STAGED_SOURCE/"

echo "Source code staged successfully"

# Stage the .env file
cp "$SCRIPT_DIR/.env" "$SCRIPT_DIR/stage-custom/03-carputer/files/.env"

# Clean up any previous pi-gen directory
[ -d "$SCRIPT_DIR/pi-gen" ] && rm -rf "$SCRIPT_DIR/pi-gen"

echo ""
echo "Cloning pi-gen (arm64 branch)..."
git clone --depth 1 --single-branch --branch "$PIGEN_BRANCH" "$PIGEN_REPO" "$SCRIPT_DIR/pi-gen"

# Copy custom stages into pi-gen
cp -r "$SCRIPT_DIR/stage-custom" "$SCRIPT_DIR/pi-gen/"

# Swap in the local run script (no GitHub cloning)
echo "Configuring for local source build..."
mv "$SCRIPT_DIR/pi-gen/stage-custom/03-carputer/00-run.sh" "$SCRIPT_DIR/pi-gen/stage-custom/03-carputer/00-run-github.sh.bak"
mv "$SCRIPT_DIR/pi-gen/stage-custom/03-carputer/00-run-local.sh" "$SCRIPT_DIR/pi-gen/stage-custom/03-carputer/00-run.sh"

# Remove git from packages since we're not cloning
sed -i.bak '/^git$/d' "$SCRIPT_DIR/pi-gen/stage-custom/03-carputer/00-packages"

cd "$SCRIPT_DIR/pi-gen"

# Generate pi-gen config
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

echo ""
echo "Starting image build..."
if [[ "$(uname)" != "Linux" ]]; then
    echo "Non-Linux host detected — building via Docker (requires Docker Desktop)."
    sudo ./build-docker.sh
else
    sudo ./build.sh
fi

# Cleanup staged source after build
rm -rf "$STAGED_SOURCE"

echo ""
echo "=========================================="
echo "Image build complete!"
echo "=========================================="
echo "Output: $SCRIPT_DIR/pi-gen/deploy/"
echo ""
echo "Login credentials:"
echo "  User:     $APP_NAME"
echo "  Password: $LOGIN_PASSWORD"
echo ""
echo "Note: This image uses LOCAL source code."
echo "Docker images will be built on first boot."
echo "=========================================="
