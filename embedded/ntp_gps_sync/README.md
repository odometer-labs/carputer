# NTP/GPS Time Synchronization

Syncs the Raspberry Pi system clock from the u-blox ZED-F9P GPS receiver using **chrony** and **GPSD**.

## How It Works

```
┌──────────────┐   serial    ┌──────────┐   SHM 0 (NMEA)   ┌──────────┐
│  u-blox      │ ──────────► │  GPSD    │ ────────────────► │  chrony  │ ──► system clock
│  ZED-F9P     │  /dev/      │          │   SHM 1 (PPS)    │          │
│  GPS module  │  ttyACM0    │          │ ────────────────► │          │
└──────────────┘             └──────────┘                   └──────────┘
                                                              ▲
                                                              │ fallback
                                                     NTP pool servers
```

1. **chrony starts first** (enforced by systemd drop-in)
2. chrony initially syncs from NTP pools (if internet is available)
3. **GPSD starts** and reads NMEA/PPS data from the GPS receiver on `/dev/ttyACM0`
4. GPSD writes time to shared memory (SHM) segments:
   - **SHM 0**: NMEA sentence time (~100ms accuracy)
   - **SHM 1**: PPS pulse time (~1µs accuracy, if TIME_PULSE pin is wired)
5. chrony reads SHM and disciplines the system clock using GPS time
6. PPS is preferred when available; NMEA provides the absolute time reference

## Files

| File | Deploy Target | Purpose |
|------|--------------|---------|
| `chrony.conf` | `/etc/chrony/chrony.conf` | chrony config with SHM refclocks + NTP fallback |
| `gpsd-depends-chrony.conf` | `/etc/systemd/system/gpsd.service.d/depends-chrony.conf` | systemd drop-in: gpsd starts after chrony |

## Systemd Boot Order

```
chrony.service → gpsd.service → postgresql.service → carputer.service
```

Enforced by:
- **gpsd drop-in** (`gpsd-depends-chrony.conf`): `After=chrony.service`, `Requires=chrony.service`
- **carputer.service**: `After=chrony.service gpsd.service postgresql.service`

## Deployment

The `infrastructure/script.sh` setup script handles deployment automatically (Step 5). To deploy manually:

```bash
# Deploy chrony config (backs up existing)
sudo cp /etc/chrony/chrony.conf /etc/chrony/chrony.conf.bak
sudo cp embedded/ntp_gps_sync/chrony.conf /etc/chrony/chrony.conf

# Deploy gpsd drop-in
sudo mkdir -p /etc/systemd/system/gpsd.service.d
sudo cp embedded/ntp_gps_sync/gpsd-depends-chrony.conf \
     /etc/systemd/system/gpsd.service.d/depends-chrony.conf

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart chrony
sudo systemctl restart gpsd
```

## Verification

```bash
# Check chrony sources (look for NMEA and PPS refclocks)
chronyc sources -v

# Check chrony tracking (system clock offset and frequency)
chronyc tracking

# Verify gpsd starts after chrony
systemctl show gpsd.service | grep After= | tr ' ' '\n' | grep chrony

# Check GPSD is receiving GPS data
cgps -s
```

## Tests

Tests live in `/embedded/tests/` and validate config file correctness:

```bash
cd embedded
uv run --group dev pytest -v
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `chronyc sources` shows `?` for NMEA/PPS | GPSD not writing to SHM | Check `cgps -s` for GPS fix; verify GPSD is running |
| `chronyc sources` shows no NMEA/PPS rows | chrony.conf not deployed | Re-deploy chrony.conf and restart chrony |
| `chronyc sources` shows only NTP, no GPS | No GPS fix (indoors) | Move antenna to clear sky; GPS will appear when fix acquired |
| chrony starts but gpsd doesn't | Drop-in missing `Requires=` | Re-deploy gpsd drop-in and `systemctl daemon-reload` |
| Large clock offset on boot | Expected for cold start | `makestep 1.0 3` allows stepping; offset corrects within ~30s |
