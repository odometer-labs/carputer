# Infrastructure

**Odometer Labs — Carputer Project**

This directory contains all infrastructure configuration for the Carputer system, including systemd service definitions and the automated setup script for the Raspberry Pi 4.

---

## Directory Structure

```
infrastructure/
├── setup.sh                  # Automated environment setup script
├── systemd/
│   └── carputer.service      # systemd service for the Carputer application
└── README.md                 # This file
```

---

## Hardware

| Component | Details |
|-----------|---------|
| Primary Board | Raspberry Pi 4 |
| GPS Module | u-blox C099-F9P (ZED-F9P) |
| GPS Antenna | u-blox ANN-MB GNSS antenna |
| GPS Connection | micro-USB (data-capable cable required) |
| Storage | 32GB microSD (verified genuine) |
| Power | 5V/3A via USB-C or barrel jack |

---

## OS

**Raspberry Pi OS Lite (64-bit)** — headless, no desktop environment.

- Based on Debian Trixie
- Kernel: 6.12.x aarch64
- Package manager: `apt`
- Network manager: NetworkManager (`nmcli`)
- Init system: systemd

---

## Network Access

### Campus (PSU)

The Pi is assigned a static IP on the PSU Secure network:

```
10.200.110.128
```

**Requirements:**
- Mac must be connected to PSU Secure WiFi
- Full-tunnel VPN must be active

```bash
ssh emb_usr@10.200.110.128
```

### Hotspot / Development

When on campus VPN is unavailable or for off-campus development, connect via phone hotspot:

```bash
ssh emb_usr@<hotspot-assigned-ip>
```

Find the Pi's current IP:
```bash
# On the Pi
ip addr show wlan0
```

### USB Gadget Ethernet

The Pi can present itself as a USB ethernet adapter over its USB-C port. This requires a **data-capable USB-C cable** connected directly from the Pi's USB-C port to your Mac (not through a hub).

**Boot partition config required** (`/boot/firmware/config.txt`):
```
dtoverlay=dwc2
```

**Boot partition config required** (`/boot/firmware/cmdline.txt`):
```
# Append to the existing single line after rootwait:
modules-load=dwc2,g_ether
```

> ⚠️ Do NOT add `dr_mode=host` to the `dtoverlay=dwc2` line — this disables gadget ethernet.

Once booted with USB-C connected to Mac:
```bash
# Find the interface
ifconfig | grep -B 2 "169.254"

# SSH via link-local
ssh emb_usr@169.254.x.x

# Or via mDNS
ssh emb_usr@carputer.local
```

> **Note:** On PSU network, the campus firewall may block USB gadget ethernet connections. Use the campus IP with full-tunnel VPN instead.

---

## Setup Script

### `setup.sh`

Automates the full environment setup from a fresh Raspberry Pi OS Lite install. Idempotent — safe to run multiple times.

**What it does:**
1. Installs required packages (`vim`, `git`, `gpsd`, `gpsd-clients`, `chrony`, `postgresql`)
2. Configures gpsd (`/etc/default/gpsd`)
3. Enables and starts systemd services (`chrony`, `gpsd`, `postgresql`)
4. Clones the carputer repo to `/opt/carputer`
5. Deploys and enables `carputer.service`

**Usage:**
```bash
# On a fresh Pi with internet access
curl -O https://raw.githubusercontent.com/odometer-labs/carputer/main/infrastructure/setup.sh
bash setup.sh
```

Or after manually cloning:
```bash
bash /opt/carputer/infrastructure/setup.sh
```

> **Note:** `setup.sh` does NOT configure SSH keys for GitHub write access. See the SSH Key Setup section below.

---

## GPS Setup

### Hardware Connection

1. Connect the **ANN-MB GNSS antenna** to the **ZED-RF** connector on the C099-F9P
2. Power the C099-F9P via its **DC barrel jack (5-12V)**
3. Connect C099-F9P to Pi via **micro-USB** using a **data-capable cable**

> ⚠️ Power-only micro-USB cables are extremely common and will cause the device to not enumerate over USB. Always verify your cable carries data.

### Verify GPS Device

```bash
# Confirm u-blox devices are visible
lsusb

# Expected output includes:
# U-Blox AG C099; ZED-F9P
# U-Blox AG C099; ODIN-W2
# U-Blox AG u-blox GNSS receiver

# Confirm device node
ls /dev/ttyACM*
# Expected: /dev/ttyACM0
```

### gpsd Configuration

gpsd is configured via `/etc/default/gpsd`:

```bash
DEVICES="/dev/ttyACM0"
GPSD_OPTIONS="-F /var/run/gpsd.sock"
USBAUTO="true"
```

gpsd exposes data via:
- Unix socket: `/var/run/gpsd.sock`
- TCP: `localhost:2947`

### Test GPS Data

```bash
cgps -s
```

> A GPS fix requires clear sky visibility. Indoors or in a basement, 0-2 satellites may be visible with no fix — this is expected.

---

## systemd Services

### Service Dependency Chain

```
chronyd (time sync)
    └── gpsd (GPS daemon)
            └── postgresql (database)
                    └── carputer (FastAPI backend)
```

### `carputer.service`

Manages the Carputer FastAPI backend application.

**Location in repo:** `infrastructure/systemd/carputer.service`
**Deployed to:** `/etc/systemd/system/carputer.service`

**Key configuration:**
| Field | Value |
|-------|-------|
| User | `emb_usr` |
| WorkingDirectory | `/opt/carputer` |
| ExecStart | `/opt/carputer/venv/bin/python -m api.src.main` |
| Restart | `always` (10s delay) |
| Watchdog | 60 seconds |

**Depends on:**
- `network.target`
- `postgresql.service`
- `gpsd.service`

**Common commands:**
```bash
# Check status
sudo systemctl status carputer

# Start / stop / restart
sudo systemctl start carputer
sudo systemctl stop carputer
sudo systemctl restart carputer

# View logs
sudo journalctl -u carputer -f
```

### Native Services (managed by apt)

| Service | Purpose | Config |
|---------|---------|--------|
| `gpsd.service` | GPS daemon | `/etc/default/gpsd` |
| `gpsd.socket` | Socket activation for gpsd | `/usr/lib/systemd/system/gpsd.socket` |
| `chrony.service` | High-precision NTP time sync | `/etc/chrony/chrony.conf` |
| `postgresql.service` | PostgreSQL database | `/etc/postgresql/` |

---

## Repository Deployment

### Location

The repo is deployed to `/opt/carputer` on the Pi.

### Ownership

```bash
sudo chown -R emb_usr:emb_usr /opt/carputer
```

### Updating

```bash
cd /opt/carputer
git pull
```

If `carputer.service` was modified:
```bash
sudo cp /opt/carputer/infrastructure/systemd/carputer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart carputer
```

---

## SSH Key Setup (GitHub Write Access)

> This step is NOT automated by `setup.sh` as it requires manual GitHub configuration.

```bash
# Generate key on the Pi
ssh-keygen -t ed25519 -C "carputer-pi4"

# Display public key
cat ~/.ssh/id_ed25519.pub
```

Add the public key as a **Deploy Key** in the GitHub repo:
- GitHub → repo → Settings → Deploy keys → Add deploy key
- Title: `carputer-pi4`
- Allow write access: **unchecked** (read-only)

Test the connection:
```bash
ssh -T git@github.com
# Expected: Hi odometer-labs/carputer! You've successfully authenticated...
```

---

## Known Issues and Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| GPS module not in `lsusb` | Power-only micro-USB cable | Swap cable |
| `lsusb` shows no u-blox devices | Wrong USB port on C099-F9P | Use the micro-USB port, not the barrel jack |
| SSH hangs on `carputer.local` | PSU firewall blocking mDNS | Use campus IP with full-tunnel VPN |
| USB gadget ethernet drops | `dr_mode=host` in `config.txt` | Remove `,dr_mode=host` from dtoverlay line |
| `carputer.service` fails to start | Python venv not set up | Install backend dependencies first |
| SD card shows wrong capacity | Counterfeit card | Replace with verified Samsung/SanDisk |
| chrony shows "no selectable sources" | Hotspot briefly disconnected | Resolves automatically when network stabilizes |

---

## Team Contacts

| Team | Responsibility |
|------|---------------|
| Embedded | GPS hardware, gpsd, systemd services, `setup.sh` |
| Backend | FastAPI, PostgreSQL schema, gpsd client code |
| Frontend | Svelte UI |
| Infrastructure | Service definitions, deployment, network config |
