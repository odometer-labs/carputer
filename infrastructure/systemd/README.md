# Systemd Services

This directory contains systemd service files for automatic startup of the Carputer application on Raspberry Pi.
This is for manual control. HIGHLY recommend to use `setup.sh` in `infrastructure/`

## Services

| Service | Description |
|---------|-------------|
| `carputer.service` | Main Carputer application (Docker Compose stack) |

## Installation

Copy service files to the systemd directory:

```bash
sudo cp *.service /etc/systemd/system/
sudo systemctl daemon-reload
```

## Enable Services

Enable services to start on boot:

```bash
sudo systemctl enable carputer.service
```

## Usage

```bash
# Start services
sudo systemctl start carputer.service

# Check status
sudo systemctl status carputer.service

# View logs
journalctl -u carputer.service -f
```

## Prerequisites

- Python virtual environment at `/opt/carputer/venv`
- PostgreSQL installed and running
- GPS module connected to `/dev/ttyACM0`
- gpsd package installed (`sudo apt install gpsd`)

## Troubleshooting

**Service fails to start:**
```bash
journalctl -u carputer.service -n 50 --no-pager
```

**GPS device not found:**
- Check USB connection: `ls -la /dev/ttyACM*`
- Verify gpsd config: `cat /etc/default/gpsd`
