# Infrastructure Team Tech Stack Recommendations

## Overview
This document outlines the recommended technology stack for the Infrastructure Team responsible for network management, offline map systems, system updates, deployment automation, and overall system reliability for the Raspberry Pi GPS Tracking Carputer project.

---

## Network Management

### WiFi Hotspot & Network Switching

#### Network Manager
- **NetworkManager** (Primary choice)
  - Built-in WiFi access point (AP) mode
  - Automatic connection to known networks
  - Easy CLI and D-Bus API
  - nmcli for scripting
  - Network priority management

**Alternative:**
- **systemd-networkd** + **hostapd** + **dnsmasq**
  - More manual configuration
  - Greater control over network stack
  - Good for minimal systems

#### Hotspot Configuration
```bash
# NetworkManager hotspot creation
nmcli device wifi hotspot \
  ssid "Carputer-Hotspot" \
  password "yourpassword" \
  ifname wlan0
```

#### Automatic Network Switching Logic
```python
# Pseudocode for network switching
if known_networks_available():
    connect_to_strongest_known_network()
else:
    enable_hotspot_mode()
```

**Implementation Tools:**
- **Python** script with NetworkManager D-Bus API
- **nm-dispatcher** scripts for network event handling
- **systemd service** for network monitoring daemon

### DNS & Service Discovery

#### mDNS/DNS-SD
- **Avahi** (mDNS/Bonjour)
  - Advertise services on local network
  - Enable `raspberrypi.local` hostname resolution
  - Service discovery for web interface

```bash
# Example avahi service file
# /etc/avahi/services/carputer.service
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>Carputer Web Interface</name>
  <service>
    <type>_http._tcp</type>
    <port>80</port>
  </service>
</service-group>
```

#### DHCP Server
- **dnsmasq** - DHCP and DNS for hotspot mode
  - Lightweight, easy configuration
  - Built-in TFTP server (if needed)
  - DNS caching

---

## Offline Map System

### Map Tile Server Options

#### Option 1: Vector Tiles (Recommended)
**Tileserver-GL**
- Serves vector tiles (Mapbox Vector Tiles format)
- Lower storage requirements than raster tiles
- Client-side rendering (lighter server load)
- Supports Mapbox GL JS and MapLibre GL JS

**Storage Requirements:**
- Full planet: ~100GB
- US only: ~10-15GB
- Regional (Pacific Northwest): ~2-5GB

**Data Sources:**
- **OpenMapTiles** - Pre-generated vector tiles
- **Planetiler** - Generate your own vector tiles from OSM data

#### Option 2: Raster Tiles
**Tile Server Stack:**
- **PostgreSQL + PostGIS** - Store OSM data
- **osm2pgsql** - Import OSM data into PostgreSQL
- **Mapnik** - Render tiles
- **renderd** + **mod_tile** - Serve tiles via Apache/nginx
- **tirex** - Alternative tile rendering daemon

**Storage Requirements:**
- Much larger than vector tiles
- Full planet at zoom 0-18: Several TB
- Regional approach recommended

**Alternative Simpler Option:**
- **TileStache** - Python tile server
- Pre-render tiles with **tilestache-seed**
- Serve static tiles with nginx

#### Option 3: Hybrid Approach (Best for Carputer)
**MBTiles + Static Tile Server**
- Download pre-rendered tiles as MBTiles files
- Use **mbtileserver** or custom Python server
- Lower CPU usage (no rendering)
- Moderate storage (download only needed regions)

**Recommended Setup:**
```
nginx (or Caddy) → Tile cache → mbtileserver → MBTiles files
```

### Map Tile Caching

#### Nginx Caching
```nginx
proxy_cache_path /var/cache/nginx/tiles 
    levels=1:2 
    keys_zone=tiles:100m 
    max_size=10g 
    inactive=365d;

location /tiles/ {
    proxy_cache tiles;
    proxy_cache_valid 200 365d;
    proxy_pass http://localhost:8080;
}
```

### Map Data Download Tools

#### OpenStreetMap Extracts
- **Geofabrik** - Regional OSM extracts (free)
- **BBBike** - Custom area extracts
- **Protomaps** - Pre-built vector tile extracts

#### Tile Downloaders
- **pyrosm** - Python library for OSM data
- **wget** or **curl** - Batch download tile archives
- **Custom Python script** - Download tiles for specific zoom levels/bounds

```python
# Example tile download script
import requests
from pathlib import Path

def download_tiles(bounds, zoom_levels):
    for z in zoom_levels:
        for x in range(x_min, x_max):
            for y in range(y_min, y_max):
                url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                # Download and save tile
```

---

## System Updates & Maintenance

### Package Management

#### Unattended Upgrades
```bash
# Install unattended-upgrades
apt install unattended-upgrades

# Configure automatic security updates
dpkg-reconfigure -plow unattended-upgrades
```

**Configuration:**
```
# /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};

Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Mail "admin@carputer.local";
```

#### Custom Update Mechanism
**For application-specific updates:**
- Git-based deployment (pull from repository)
- Rsync from update server
- Custom package repository (apt-ftparchive)

### System Health Monitoring

#### Monitoring Tools
- **Prometheus** + **Node Exporter** (heavyweight but comprehensive)
- **Netdata** (lightweight, real-time monitoring)
- **Custom Python scripts** (simplest approach)

**Metrics to Monitor:**
- CPU temperature (important for automotive environment)
- Disk space usage
- Memory usage
- GPS fix status
- Database size
- Network connectivity
- Service health (systemd unit status)

#### Health Check Script
```python
#!/usr/bin/env python3
import psutil
import subprocess

def check_system_health():
    return {
        "cpu_temp": get_cpu_temperature(),
        "disk_usage": psutil.disk_usage('/').percent,
        "memory_usage": psutil.virtual_memory().percent,
        "gps_status": check_gps_lock(),
        "db_size": get_database_size(),
        "uptime": get_uptime(),
    }
```

### Log Management

#### Logging Strategy
- **systemd journal** - Primary log storage
  - `journalctl -u service-name`
  - Automatic rotation
  - Persistent storage configuration

**Configuration:**
```ini
# /etc/systemd/journald.conf
[Journal]
Storage=persistent
SystemMaxUse=500M
MaxRetentionSec=1month
```

#### Log Rotation
- **logrotate** - For application logs
```
# /etc/logrotate.d/carputer
/var/log/carputer/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## Deployment & Image Building

### SD Card Image Creation

#### Option 1: pi-gen (Official Raspberry Pi Tool)
- Fork of official Raspberry Pi OS builder
- Customizable stages for software installation
- Produces `.img` files ready to flash

**Basic Structure:**
```
pi-gen/
├── stage0/  # Base system
├── stage1/  # Basic packages
├── stage2/  # Desktop environment (skip for lite)
├── stage-carputer/
│   ├── 00-install-packages/
│   ├── 01-configure-system/
│   └── 02-install-app/
└── config  # Build configuration
```

#### Option 2: Packer
- HashiCorp tool for building machine images
- ARM plugin for Raspberry Pi images
- Provisioners for Ansible, shell scripts

**Example Packer Template:**
```json
{
  "builders": [{
    "type": "arm",
    "file_urls": ["https://downloads.raspberrypi.org/..."],
    "file_target_extension": "zip",
    "image_build_method": "resize",
    "image_size": "8G",
    "image_type": "dos"
  }],
  "provisioners": [{
    "type": "shell",
    "script": "setup.sh"
  }]
}
```

#### Option 3: Custom Bash Script
**Simple approach for smaller teams:**
```bash
#!/bin/bash
# Mount existing Raspberry Pi OS image
# chroot into mounted filesystem
# Run installation commands
# Unmount and compress
```

### Configuration Management

#### Ansible (Recommended)
```yaml
# playbook.yml
---
- hosts: carputer
  become: yes
  roles:
    - base-system
    - network-config
    - gps-setup
    - database
    - backend-api
    - frontend
    - map-server
```

**Advantages:**
- Idempotent operations
- Easy to version control
- Reusable roles
- Can apply to existing systems or during image build

#### Alternative: Shell Scripts
- Simpler for small projects
- Less abstraction, more direct
- Good for one-time setup

```bash
#!/bin/bash
# install.sh
set -e

source lib/common.sh
source lib/network.sh
source lib/database.sh

install_base_packages
configure_network
setup_database
install_backend
install_frontend
```

---

## Container Strategy (Optional)

### Docker Considerations

**Pros:**
- Isolated services
- Easy updates (pull new images)
- Consistent environments
- Simplified dependency management

**Cons:**
- Overhead on Raspberry Pi
- Complexity for hardware access (GPS, SDR)
- Storage space for images

**Recommended Approach:**
- **Docker for stateless services** (backend API, map server)
- **Native installation for hardware services** (gpsd, direwolf)

#### Docker Compose Example
```yaml
version: '3.8'
services:
  backend:
    image: carputer/backend:latest
    ports:
      - "8000:8000"
    volumes:
      - /var/lib/carputer:/data
    depends_on:
      - postgres
  
  postgres:
    image: postgis/postgis:15-3.3
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: changeme
  
  map-server:
    image: maptiler/tileserver-gl:latest
    ports:
      - "8080:80"
    volumes:
      - ./map-data:/data

volumes:
  pgdata:
```

**Alternative: Podman**
- Daemonless container runtime
- Rootless containers
- Drop-in replacement for Docker

---

## System Hardening & Security

### Firewall Configuration

#### UFW (Uncomplicated Firewall)
```bash
# Enable firewall
ufw enable

# Allow SSH (if needed for maintenance)
ufw allow 22/tcp

# Allow web interface
ufw allow 80/tcp
ufw allow 443/tcp

# Allow mDNS
ufw allow 5353/udp

# Default deny incoming
ufw default deny incoming
ufw default allow outgoing
```

#### nftables (Modern alternative)
- Replaces iptables
- More efficient rule matching
- Better syntax

### SSH Hardening
```
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 2222  # Non-standard port
AllowUsers pi
```

### Automatic Security Updates
Already covered in System Updates section with unattended-upgrades

### File System Security
- **Mount /tmp with noexec**
- **Enable AppArmor** (or SELinux)
- **Regular filesystem checks** (BTRFS or ext4 with fsck)

---

## Backup & Recovery

### Backup Strategy

#### What to Backup
- **Database** - Track data, APRS logs
- **Configuration files** - /etc/carputer/, systemd units
- **User data** - Imported tracks, custom settings
- **System image** (periodic) - For disaster recovery

#### Backup Tools

**Database Backups:**
```bash
# PostgreSQL dump
pg_dump -U carputer carputer_db | gzip > backup.sql.gz

# Automated with cron
0 2 * * * /usr/local/bin/backup-database.sh
```

**File Backups:**
- **rsync** - Incremental backups to USB drive or network share
- **restic** - Encrypted, deduplicated backups
- **borgbackup** - Similar to restic

```bash
# Rsync to USB drive
rsync -avz /var/lib/carputer/ /mnt/usb/backups/
```

#### Recovery Strategy
1. **Full system recovery** - Flash SD card image, restore database
2. **Partial recovery** - Restore specific configuration files or database
3. **Rollback mechanism** - Keep N previous SD card images for emergency reflash

---

## Boot Optimization

### Reduce Boot Time

#### Disable Unnecessary Services
```bash
# Identify slow services
systemd-analyze blame

# Disable unneeded services
systemctl disable bluetooth.service
systemctl disable ModemManager.service
systemctl disable avahi-daemon.service  # if not using mDNS
```

#### Enable Parallel Startup
```ini
# /etc/systemd/system.conf
DefaultTimeoutStartSec=10s
DefaultTimeoutStopSec=10s
```

#### Optimize Filesystem
- Use **f2fs** or **ext4** on SD card
- Enable **noatime** mount option (reduces writes)

```
# /etc/fstab
/dev/mmcblk0p2 / ext4 defaults,noatime,commit=60 0 1
```

### Auto-start Application
**Systemd service:**
```ini
# /etc/systemd/system/carputer-ui.service
[Unit]
Description=Carputer Touch Interface
After=graphical.target

[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
Type=simple
User=pi
ExecStart=/usr/bin/chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:8000
Restart=always

[Install]
WantedBy=graphical.target
```

---

## Power Management

### Automotive Environment Considerations

#### Clean Shutdown on Power Loss
**UPS HAT Integration:**
- PiJuice HAT
- Geekworm X728 UPS
- Waveshare UPS HAT

**Monitoring Script:**
```python
# Monitor power status and initiate clean shutdown
import RPi.GPIO as GPIO
import os

POWER_LOSS_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(POWER_LOSS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def power_loss_callback(channel):
    print("Power loss detected, shutting down...")
    os.system("sudo shutdown -h now")

GPIO.add_event_detect(POWER_LOSS_PIN, GPIO.FALLING, 
                      callback=power_loss_callback, 
                      bouncetime=2000)
```

#### Delayed Shutdown
- Keep system running for N minutes after ignition off
- Save battery by shutting down completely after timeout

### Reduce Power Consumption
- Disable HDMI when not needed: `/usr/bin/tvservice -o`
- Undervolt CPU if performance permits
- Disable unused USB ports
- Use power-efficient kernel (realtime patches if needed)

---

## CI/CD for Image Building

### GitHub Actions Workflow

```yaml
# .github/workflows/build-image.yml
name: Build Carputer Image

on:
  push:
    branches: [ main ]
  release:
    types: [ created ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y qemu-user-static
      
      - name: Build image with pi-gen
        run: |
          ./build-image.sh
      
      - name: Compress image
        run: |
          xz -9 -T0 carputer.img
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: carputer-image
          path: carputer.img.xz
      
      - name: Create release
        if: github.event_name == 'release'
        uses: actions/upload-release-asset@v1
        with:
          upload_url: ${{ github.event.release.upload_url }}
          asset_path: carputer.img.xz
          asset_name: carputer-${{ github.event.release.tag_name }}.img.xz
          asset_content_type: application/x-xz
```

### Image Versioning
- Semantic versioning: `v1.0.0`
- Include build date in filename: `carputer-v1.0.0-20250202.img.xz`
- Maintain changelog

---

## Documentation & Installation Guide

### Documentation Tools
- **MkDocs** - Static site generator for documentation
  - Material theme for modern UI
  - Easy markdown-based content

```yaml
# mkdocs.yml
site_name: Carputer Documentation
theme:
  name: material
nav:
  - Home: index.md
  - Installation: installation.md
  - Configuration: configuration.md
  - API Reference: api.md
  - Troubleshooting: troubleshooting.md
```

### Installation Script
```bash
#!/bin/bash
# install.sh - Quick installation on existing Raspberry Pi

echo "Carputer Installation Script"
echo "============================"

# Check system compatibility
check_compatibility

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
install_dependencies

# Configure network
setup_network_hotspot

# Install database
setup_postgresql_postgis

# Install backend
install_backend_api

# Install frontend
install_frontend

# Configure services
setup_systemd_services

# Download map data
download_map_tiles

echo "Installation complete!"
echo "Access web interface at: http://raspberrypi.local"
```

---

## Recommended Full Stack

```
Operating System:
├── Raspberry Pi OS Lite (64-bit)
└── Kernel 6.1+ with realtime patches (optional)

Network Management:
├── NetworkManager (WiFi switching & hotspot)
├── dnsmasq (DHCP server for hotspot)
└── Avahi (mDNS service discovery)

Map System:
├── Tileserver-GL (vector tiles) - OR
├── mbtileserver (MBTiles files) - OR
└── nginx + static tiles (simplest)

System Updates:
├── unattended-upgrades (security updates)
├── Custom update script (application updates)
└── systemd timers (scheduled tasks)

Monitoring:
├── Custom Python health check scripts
├── systemd journal (logging)
└── logrotate (log management)

Deployment:
├── pi-gen or Packer (image building)
├── Ansible (configuration management)
├── GitHub Actions (CI/CD)
└── rsync or restic (backups)

Security:
├── UFW (firewall)
├── SSH hardening
├── AppArmor (MAC)
└── Automatic security updates

Web Server:
├── nginx (recommended) - OR
└── Caddy (simpler, automatic HTTPS)
```

---

## Performance Targets

### Boot Time Goals
- Power-on to UI ready: < 60 seconds
- Power-on to GPS lock: < 90 seconds
- Service startup time: < 5 seconds each

### Network Goals
- Hotspot activation: < 10 seconds
- Network switch time: < 15 seconds
- mDNS response time: < 1 second

### Map Server Goals
- Tile serving: < 100ms per tile
- Map view load: < 2 seconds
- Cache hit rate: > 90% for frequently accessed areas

---

## Storage Management

### Disk Space Allocation
```
Total 32GB SD Card:
├── System (OS): ~4GB
├── Database: ~2-5GB (grows with usage)
├── Map tiles: ~10-15GB (configurable)
├── Application: ~1GB
├── Logs: ~500MB (with rotation)
└── Free space: ~10GB (safety margin)
```

### Cleanup Scripts
```bash
#!/bin/bash
# cleanup.sh - Free up disk space

# Clean apt cache
sudo apt-get clean

# Remove old journal logs
sudo journalctl --vacuum-time=7d

# Clean old APRS data (>30 days)
psql -U carputer -c "DELETE FROM aprs_history WHERE timestamp < NOW() - INTERVAL '30 days';"

# Remove old map tile cache
find /var/cache/tiles -type f -mtime +90 -delete
```

---

## Troubleshooting Tools

### System Diagnostic Script
```bash
#!/bin/bash
# diagnose.sh - System health check

echo "=== System Information ==="
uname -a
cat /etc/os-release

echo "=== CPU Temperature ==="
vcgencmd measure_temp

echo "=== Disk Usage ==="
df -h

echo "=== Memory Usage ==="
free -h

echo "=== Service Status ==="
systemctl status gpsd
systemctl status carputer-backend
systemctl status postgresql

echo "=== GPS Status ==="
cgps -s

echo "=== Network Status ==="
ip addr
nmcli connection show

echo "=== Recent Errors ==="
journalctl -p err -n 50
```

### Common Issues & Solutions
Document common problems:
- GPS not getting fix (antenna placement, cold start)
- WiFi hotspot not starting (NetworkManager conflicts)
- Database connection errors (PostgreSQL not started)
- Map tiles not loading (storage full, service down)

---

## Testing Strategy

### Integration Testing
- **Boot test** - Verify system boots correctly
- **Network test** - Test hotspot and network switching
- **GPS test** - Verify GPS lock and data flow
- **Map test** - Verify tile serving
- **API test** - Test backend endpoints
- **End-to-end test** - Complete user workflow

### Automated Testing
```bash
#!/bin/bash
# test-deployment.sh

# Flash test image to SD card
# Boot Raspberry Pi
# Wait for system to be ready
# Run test suite
# Collect results
```

### Performance Testing
- Boot time measurement
- Tile serving benchmarks
- Database query performance
- Network throughput tests

---

## Maintenance Schedule

### Daily Tasks (Automated)
- Health check monitoring
- Log rotation
- Database backup

### Weekly Tasks (Automated)
- System updates check
- Disk space monitoring
- Service restart (if needed)

### Monthly Tasks (Manual)
- Review logs for issues
- Update map data
- Performance review
- Security audit

### Quarterly Tasks (Manual)
- Full system backup
- Software version updates
- Hardware inspection (automotive environment)

---

## Hardware Recommendations

### Raspberry Pi Selection
- **Raspberry Pi 4 (4GB)** - Recommended for development
- **Raspberry Pi 5** - Better performance, may have compatibility issues
- **Raspberry Pi CM4** - For production, compact form factor

### SD Card Recommendations
- **Endurance cards** preferred (Samsung PRO Endurance, SanDisk High Endurance)
- 32GB minimum, 64GB recommended
- A2 application performance class
- Regular backups (SD cards fail in automotive environments)

### Cooling Solutions
- Heat sinks (minimum)
- Active cooling fan (recommended for enclosed installations)
- Temperature monitoring critical

---

## Next Steps

1. **Set up build environment**
   - Install pi-gen or Packer
   - Configure Ansible playbooks
   - Set up version control

2. **Network configuration**
   - Configure NetworkManager hotspot
   - Test network switching logic
   - Set up mDNS

3. **Map system selection**
   - Choose tile server approach
   - Download initial map data
   - Configure tile caching

4. **Deployment pipeline**
   - Create GitHub Actions workflow
   - Build initial SD card image
   - Test installation script

5. **System hardening**
   - Configure firewall
   - Enable automatic updates
   - Set up monitoring

6. **Documentation**
   - Write installation guide
   - Create troubleshooting guide
   - Document maintenance procedures

---

## Additional Resources

- **Raspberry Pi OS Documentation:** https://www.raspberrypi.com/documentation/
- **NetworkManager Documentation:** https://networkmanager.dev/
- **pi-gen Repository:** https://github.com/RPi-Distro/pi-gen
- **OpenStreetMap Tile Serving:** https://switch2osm.org/
- **Ansible Documentation:** https://docs.ansible.com/
- **systemd Documentation:** https://www.freedesktop.org/wiki/Software/systemd/
- **Tileserver-GL:** https://github.com/maptiler/tileserver-gl
