# Carputer Image Builder

Builds a Raspbian arm64 image with the carputer stack pre-installed, using [pi-gen](https://github.com/rpi-distro/pi-gen).

The image targets CM4-based hardware (e.g. Seeed Studio ReTerminal). Two build modes are available:

| Mode | Script | Source | Docker Images |
|------|--------|--------|---------------|
| **Local** | `generate_image_local.sh` | Copies from your machine | Built on Pi at first boot |
| **GitHub** | `generate_image.sh` | Clones from GitHub | Pulls from ghcr.io |

---

## Local Build (No GitHub)

Use this to build an image from your local source code without any GitHub interaction.

### Prerequisites

#### 1. `.env` file

Copy `.env.example` from the project root into this directory:

```bash
cp ../../.env.example .env
```

Set at minimum:

```
POSTGRES_USER=carputer
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=carputer
```

#### 2. Docker Desktop

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and make sure it is running.

### Building (Local)

```bash
cd infrastructure/image-builder
chmod +x generate_image_local.sh
./generate_image_local.sh
```

The script will:
1. Copy your local source code (excluding `.git`, `node_modules`, etc.)
2. Clone pi-gen (arm64 branch)
3. Build the image via Docker
4. Print the generated login password when done

Output image: `./pi-gen/deploy/`

### First-boot behaviour (Local)

On first boot, systemd starts `carputer.service` which runs:

```
docker compose -f /opt/carputer/docker-compose.local.yml up -d --build
```

This builds all Docker images locally on the Pi from the copied source code. **First boot takes longer** (10-20 minutes) due to image compilation.

---

## GitHub Build (Production)

Use this for production deployments that pull pre-built images from the container registry.

### Prerequisites

#### 1. SSH deploy key

Generate a key and add the public half to the carputer GitHub repo as a read-only deploy key:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/carputer_deploy -C "carputer-image-builder" -N ""
# Add ~/.ssh/carputer_deploy.pub to GitHub → Settings → Deploy keys (read-only)
```

#### 2. `.env` file

Copy `.env.example` from the project root into this directory and fill in your values:

```bash
cp ../../.env.example .env
```

Set at minimum:

```
POSTGRES_USER=carputer
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=carputer
CARPUTER_DEPLOY_KEY=/absolute/path/to/private/key   # e.g. /Users/you/.ssh/carputer_deploy
```

#### 3. Docker Desktop

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and make sure it is running.

### Building (GitHub)

```bash
cd infrastructure/image-builder
./generate_image.sh
```

The script will:
1. Clone pi-gen (arm64 branch)
2. Inject your deploy key and custom stages
3. Build the image via Docker
4. Print the generated login password when done

Output image: `./pi-gen/deploy/`

### First-boot behaviour (GitHub)

On the Pi, systemd starts `carputer.service` which runs:

```
docker compose -f /opt/carputer/docker-compose.prod.yml up -d
```

This pulls pre-built images for `api` and `frontend` from `ghcr.io/odometer-labs/`, and builds `gpsd-service` and `wifi-manager` from the cloned repo source.

---

> **Note:** Each run deletes any existing `pi-gen/` directory and rebuilds from scratch.
