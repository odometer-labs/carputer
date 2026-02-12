# Infrastructure Team Epics

**Version:** 1.0  
**Date:** February 1, 2026  
**Team:** Infrastructure  
**Timeline:** 12-14 weeks (February 2026 - May 2026)

---

## Epic Overview

| Epic ID | Epic Name | Duration | Dependencies |
|---------|-----------|----------|--------------|
| INFRA-E1 | Development Environment & CI/CD Foundation | Weeks 1-2 | None |
| INFRA-E2 | Database Infrastructure | Weeks 2-4 | INFRA-E1 |
| INFRA-E3 | System Services & Boot Configuration | Weeks 4-6 | INFRA-E1, INFRA-E2 |
| INFRA-E4 | Network & Connectivity Infrastructure | Weeks 5-7 | INFRA-E3 |
| INFRA-E5 | Offline Map Tile Infrastructure | Weeks 6-8 | INFRA-E2 |
| INFRA-E6 | SD Card Image Build System | Weeks 8-11 | INFRA-E1 through E5, INFRA-E9 |
| INFRA-E7 | Monitoring, Logging & Reliability | Weeks 9-11 | INFRA-E3 |
| INFRA-E8 | Documentation & Handoff | Weeks 12-14 | All |
| INFRA-E9 | CAN Bus & Sensor Fusion Infrastructure | Weeks 5-7 | INFRA-E3 |

---

## INFRA-E1: Development Environment & CI/CD Foundation

**Duration:** Weeks 1-2  
**Owner:** TBD  
**Priority:** Critical Path

### Description
Establish the foundational development environment, CI/CD pipelines, and repository standards that will support all other infrastructure work and development team activities.

### User Stories

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| INFRA-1.1 | As a developer, I need a standardized dev environment setup so I can start contributing quickly | 5 | Docker Compose dev environment works on macOS/Linux; documented in README |
| INFRA-1.2 | As a developer, I need automated linting and testing on PRs so code quality is enforced | 3 | GitHub Actions runs pytest, pylint, black on every PR |
| INFRA-1.3 | As a team lead, I need branch protection rules so main stays stable | 2 | PRs required; CI must pass; 1 approval needed |
| INFRA-1.4 | As a developer, I need a local test database so I can develop without affecting production | 3 | Docker Compose includes PostGIS; test data seeding script works |
| INFRA-1.5 | As a developer, I need pre-commit hooks so issues are caught before push | 2 | pre-commit config with black, isort, pylint hooks |
| INFRA-1.6 | As a team, we need dependency management so builds are reproducible | 2 | requirements.txt pinned; dependabot configured |

### Definition of Done
- [ ] GitHub Actions CI pipeline passing on all PRs
- [ ] Docker Compose dev environment documented and tested
- [ ] Branch protection rules enabled on main
- [ ] Pre-commit hooks configured and documented
- [ ] Dependabot alerts enabled

### Risks
| Risk | Mitigation |
|------|------------|
| CI runner costs | Use GitHub free tier; optimize job caching |
| Docker complexity for team | Provide detailed onboarding docs |

---

## INFRA-E2: Database Infrastructure

**Duration:** Weeks 2-4  
**Owner:** TBD  
**Priority:** Critical Path

### Description
Deploy and configure PostgreSQL with PostGIS extension, establish database schema migrations, backup strategies, and performance optimization for spatial queries.

### User Stories

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| INFRA-2.1 | As a system, I need PostgreSQL + PostGIS installed so spatial data can be stored | 5 | Automated installation via setup.sh; PostGIS extension enabled |
| INFRA-2.2 | As a developer, I need database migrations so schema changes are versioned | 5 | Alembic or equivalent configured; migration scripts in repo |
| INFRA-2.3 | As an operator, I need automated database backups so data isn't lost | 3 | Daily pg_dump cron job; backup rotation (7 daily, 4 weekly) |
| INFRA-2.4 | As a system, I need optimized spatial indexes so queries are fast | 3 | GIST indexes on all geography columns; query performance < 100ms |
| INFRA-2.5 | As a developer, I need a database seeding script so I can test with realistic data | 3 | Seed script creates sample tracks, APRS positions |
| INFRA-2.6 | As an operator, I need database connection pooling so the app handles load | 3 | PgBouncer or equivalent configured |
| INFRA-2.7 | As an operator, I need database storage estimates so I can plan capacity | 2 | Documentation: estimated storage per year of use |

### Definition of Done
- [ ] PostgreSQL 15+ with PostGIS 3.3+ installed and configured
- [ ] All schema migrations versioned and automated
- [ ] Backup cron job running; restore tested
- [ ] Spatial indexes optimized; benchmarks documented
- [ ] Seed data script working

### Risks
| Risk | Mitigation |
|------|------------|
| PostGIS performance on Pi 4 | Benchmark early; tune shared_buffers/work_mem |
| SD card write wear from DB | Use high-endurance card; tune checkpoint intervals |

---

## INFRA-E3: System Services & Boot Configuration

**Duration:** Weeks 4-6  
**Owner:** TBD  
**Priority:** Critical Path

### Description
Configure systemd services for all application components, implement auto-start on boot, watchdog monitoring, and graceful shutdown handling for power loss scenarios. Configure hardware interfaces including GPS (via gpsd), RTL-SDR for APRS reception, and CAN bus adapters for vehicle data. Set up the APRS receiver pipeline (rtl_fm + direwolf/multimon-ng) with configurable frequency and database integration. Apply security hardening to all services.

### User Stories

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| INFRA-3.1 | As a user, I need the app to start automatically on boot so I don't have to configure anything | 5 | systemd services enabled; app running within 60s of power-on |
| INFRA-3.2 | As a system, I need a watchdog so crashed services restart automatically | 3 | systemd watchdog configured; tested service recovery < 30s |
| INFRA-3.3 | As a system, I need graceful shutdown on power loss so data isn't corrupted | 5 | systemd shutdown hooks; DB sync before power off |
| INFRA-3.4 | As an operator, I need service dependencies ordered correctly so startup is reliable | 3 | After= and Wants= configured; startup order tested |
| INFRA-3.5 | As a developer, I need GPSD configured so GPS hardware is accessible | 3 | gpsd service configured; auto-detects USB GPS |
| INFRA-3.6 | As a developer, I need RTL-SDR udev rules so SDR hardware is accessible | 2 | udev rules installed; non-root access to SDR device |
| INFRA-3.7 | As an operator, I need service security hardening so the system is protected | 3 | NoNewPrivileges, ProtectSystem, ProtectHome configured |
| INFRA-3.8 | As a developer, I need CAN bus interfaces configured so vehicle data is accessible | 3 | SocketCAN or OBD-II adapter accessible; udev rules installed |
| INFRA-3.9 | As a developer, I need the APRS receiver service configured so I can receive amateur radio positions | 5 | rtl_fm + direwolf/multimon-ng pipeline working; systemd service enabled |
| INFRA-3.10 | As the APRS service, I need proper audio pipeline configuration so packet decoding works | 3 | ALSA loopback or pipe configured; rtl_fm output routed to decoder |
| INFRA-3.11 | As an operator, I need APRS frequency configurable so I can tune to local digipeaters | 2 | Config file supports frequency setting; default 144.390 MHz (NA) |
| INFRA-3.12 | As the app, I need decoded APRS packets available via API so the map can display them | 3 | APRS service writes to DB; REST endpoint returns recent packets |

### Definition of Done
- [ ] All services start automatically on boot
- [ ] Watchdog tested: kill -9 service → auto-restart
- [ ] Graceful shutdown tested with simulated power loss
- [ ] GPS and SDR hardware accessible to application
- [ ] CAN bus interface accessible (OBD-II or SocketCAN)
- [ ] APRS receiver service running and decoding packets
- [ ] APRS packets stored in database and accessible via API
- [ ] Security hardening applied to all services

### Technical Notes: APRS Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  RTL-SDR    │────►│   rtl_fm    │────►│  direwolf   │────►│  carputer   │
│  Hardware   │     │  (FM demod) │     │  (AX.25     │     │  APRS svc   │
│  144.39 MHz │     │  -f 144390k │     │   decode)   │     │  → DB       │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Alternative pipeline (lighter weight):**
```
rtl_fm → multimon-ng -a AFSK1200 → parse → DB
```

### Risks
| Risk | Mitigation |
|------|------------|
| USB device detection race conditions | Add udev settle delay; test with different USB hubs |
| Power loss data corruption | Enable ext4 journaling; tune commit interval |
| RTL-SDR frequency drift | Use rtl_fm with PPM correction; calibrate with known signal |
| APRS decoding CPU usage | Use direwolf (optimized); limit to single frequency |

---

## INFRA-E4: Network & Connectivity Infrastructure

**Duration:** Weeks 5-7  
**Owner:** TBD  
**Priority:** High

### Description
Implement WiFi hotspot functionality with WPA2 security, automatic network switching between known networks and hotspot fallback mode, DNS/DHCP for hotspot clients via dnsmasq, and mDNS (avahi) for carputer.local discovery. Enable WiFi credential management via web UI API.

### User Stories

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| INFRA-4.1 | As a user, I need the carputer to create a WiFi hotspot so I can connect my phone | 5 | hostapd configured; WPA2 secured; SSID: "Carputer" |
| INFRA-4.2 | As a user, I need the carputer to auto-connect to known WiFi networks | 3 | NetworkManager configured with priority-based connection |
| INFRA-4.3 | As a system, I need fallback to hotspot mode when no networks are available | 5 | Auto-switch within 30s of losing connection |
| INFRA-4.4 | As a hotspot client, I need DHCP and DNS so my device gets an IP | 3 | dnsmasq configured; DHCP range: 192.168.4.2-20 |
| INFRA-4.5 | As an operator, I need captive portal detection disabled so clients connect properly | 2 | DNS responds correctly; no redirect loops |
| INFRA-4.6 | As an operator, I need WiFi credentials manageable via web UI | 3 | API endpoint for WiFi config; stored in config.yaml |
| INFRA-4.7 | As a developer, I need mDNS so I can access carputer.local | 2 | avahi-daemon configured; responds to carputer.local |

### Definition of Done
- [ ] Hotspot activates when no known networks available
- [ ] Known networks auto-connect with correct priority
- [ ] DHCP/DNS working for hotspot clients
- [ ] mDNS working: `ping carputer.local`
- [ ] WiFi credentials changeable via API

### Risks
| Risk | Mitigation |
|------|------------|
| WiFi driver issues on Pi | Test with built-in WiFi; document compatible dongles |
| Hotspot/client mode switching race | Implement state machine; add delays |

---

## INFRA-E5: Offline Map Tile Infrastructure

**Duration:** Weeks 6-8  
**Owner:** TBD  
**Priority:** High

### Description
Build the infrastructure for downloading, storing, and serving offline OpenStreetMap tiles for areas where internet connectivity is unavailable. Implement a tile download script with bounding box and zoom level support, efficient tile storage (MBTiles or directory structure), a local tile server with online fallback, web UI for region selection and download progress, LRU cache eviction for storage management, and OSM usage policy compliance.

### User Stories

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| INFRA-5.1 | As an operator, I need a tile download script so I can cache map regions | 5 | Script downloads tiles for bbox; supports zoom levels 1-16 |
| INFRA-5.2 | As a system, I need efficient tile storage so disk space is managed | 3 | MBTiles or directory structure; compression enabled |
| INFRA-5.3 | As the map UI, I need a local tile server so offline maps work | 5 | Tile server returns cached tiles; falls back to online |
| INFRA-5.4 | As a user, I need to select regions for offline download via web UI | 5 | Web interface for region selection; download progress shown |
| INFRA-5.5 | As an operator, I need tile cache cleanup so storage doesn't fill up | 3 | LRU cache eviction; configurable max size |
| INFRA-5.6 | As a system, I need tile download to respect OSM usage policy | 2 | Rate limiting; proper User-Agent; tile.openstreetmap.org TOS |

### Definition of Done
- [ ] Tile download script working for arbitrary regions
- [ ] Tile server serves cached tiles with sub-100ms latency
- [ ] Fallback to online tiles when cache miss
- [ ] Storage management prevents disk full
- [ ] OSM tile usage policy compliance documented

### Risks
| Risk | Mitigation |
|------|------------|
| Large tile storage requirements | Document size estimates; limit zoom levels |
| OSM tile server rate limiting | Use multiple tile sources; local rendering as stretch |

---

## INFRA-E6: SD Card Image Build System

**Duration:** Weeks 8-11  
**Owner:** TBD  
**Priority:** Critical (DEL-002, DEL-003)

### Description
Create an automated system for building ready-to-boot SD card images that include all software and configuration. Automate builds via GitHub Actions with reproducible, versioned images. Implement a first-boot configuration wizard (WiFi, password, timezone), over-the-air (OTA) update capability via web UI, and QEMU-based smoke testing in CI to prevent bad releases.

### User Stories

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| INFRA-6.1 | As a user, I need a ready-to-boot SD image so setup is zero-touch | 8 | Image boots to working app; no manual config needed |
| INFRA-6.2 | As an operator, I need the image build automated via GitHub Actions | 8 | Push to main triggers image build; artifact uploaded |
| INFRA-6.3 | As a user, I need first-boot configuration so I can set my preferences | 5 | First-boot wizard: WiFi, password, timezone |
| INFRA-6.4 | As an operator, I need image versioning so I know what's deployed | 2 | Version file in image; displayed in web UI |
| INFRA-6.5 | As an operator, I need image build reproducibility so builds are consistent | 3 | Pinned base image; deterministic package versions |
| INFRA-6.6 | As a user, I need OTA updates so I don't need to reflash the SD card | 8 | Web UI update button; downloads and applies update |
| INFRA-6.7 | As a developer, I need image testing in CI so bad images aren't released | 5 | QEMU-based smoke tests in GitHub Actions |

### Definition of Done
- [ ] SD card image builds successfully in GitHub Actions
- [ ] Image boots on Raspberry Pi 4 within 60 seconds
- [ ] First-boot wizard configures essential settings
- [ ] OTA update mechanism tested end-to-end
- [ ] Image version visible in web UI

### Risks
| Risk | Mitigation |
|------|------------|
| Image build time in CI | Use caching; incremental builds |
| GitHub Actions storage limits | Clean up old artifacts; use external storage |
| OTA update failures bricking device | Implement A/B partition scheme or recovery mode |

---

## INFRA-E7: Monitoring, Logging & Reliability

**Duration:** Weeks 9-11  
**Owner:** TBD  
**Priority:** Medium-High

### Description
Implement comprehensive logging (centralized via journald with web UI viewer), system health monitoring dashboard (GPS status, DB health, disk space, CPU/GPU temperature), alerting for thermal throttling and low disk space, log rotation to prevent disk fill, optional read-only root filesystem for SD card longevity, and systemd service status visibility in the web UI.

### User Stories

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| INFRA-7.1 | As an operator, I need centralized logging so I can debug issues | 3 | All services log to journald; web UI log viewer |
| INFRA-7.2 | As a user, I need a system health dashboard so I know things are working | 5 | Dashboard shows: GPS status, DB health, disk space, temp |
| INFRA-7.3 | As a system, I need log rotation so disk doesn't fill up | 2 | journald configured with max size; logrotate for app logs |
| INFRA-7.4 | As an operator, I need temperature monitoring so thermal issues are detected | 3 | CPU/GPU temp in dashboard; throttling alerts |
| INFRA-7.5 | As an operator, I need disk space monitoring so I'm warned before full | 3 | Alert when <10% free; visible in dashboard |
| INFRA-7.6 | As a system, I need read-only root filesystem option for reliability | 5 | Overlay filesystem optional; reduces SD card wear |
| INFRA-7.7 | As an operator, I need service status in web UI so I can see what's running | 3 | Dashboard shows all systemd service states |

### Definition of Done
- [ ] All logs accessible via web UI
- [ ] Health dashboard shows all key metrics
- [ ] Log rotation prevents disk fill
- [ ] Temperature and disk alerts working
- [ ] Read-only root option documented and testable

### Risks
| Risk | Mitigation |
|------|------------|
| Logging overhead on Pi 4 | Rate limit logs; sample high-frequency events |
| Read-only root complexity | Make it optional; document trade-offs |

---

## INFRA-E9: CAN Bus & Sensor Fusion Infrastructure

**Duration:** Weeks 5-7  
**Owner:** TBD  
**Priority:** High

### Description
Configure CAN bus hardware interfaces (OBD-II via ELM327 and SocketCAN via MCP2515) for reading vehicle data (speed, steering angle, RPM, fuel level, coolant temp). Implement Kalman filter-based sensor fusion combining GPS and CAN data for improved position tracking and dead reckoning during GPS signal loss (tunnels, urban canyons, parking structures). Display vehicle metrics in web UI dashboard, provide CAN connection status in health monitoring, support DBC files for vehicle-specific decoding, and include a simulated CAN driver for testing without hardware.

### User Stories

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| INFRA-9.1 | As a developer, I need OBD-II adapter support so I can read vehicle data | 5 | ELM327 adapter detected; python-obd configured; basic PIDs readable |
| INFRA-9.2 | As a developer, I need SocketCAN support for direct CAN access | 5 | MCP2515 SPI module configured; can-utils working; udev rules installed |
| INFRA-9.3 | As the app, I need vehicle speed from CAN so position tracking continues in tunnels | 5 | Dead reckoning maintains position within 50m over 30s GPS loss |
| INFRA-9.4 | As the app, I need steering angle from CAN so turn prediction is accurate | 3 | Heading prediction within 10° during GPS dropout |
| INFRA-9.5 | As a user, I need CAN data displayed in the UI so I can see vehicle metrics | 3 | Dashboard shows: speed, RPM, fuel level, coolant temp |
| INFRA-9.6 | As a developer, I need a simulated CAN driver for testing without hardware | 3 | SimulatedCANDriver generates realistic test data |
| INFRA-9.7 | As the app, I need sensor fusion to combine GPS and CAN for best position | 8 | Kalman filter fuses GPS + wheel speed + steering angle |
| INFRA-9.8 | As an operator, I need CAN connection status in system health dashboard | 2 | Dashboard shows CAN adapter status and data freshness |
| INFRA-9.9 | As a developer, I need DBC file support for vehicle-specific CAN decoding | 3 | cantools integration; custom DBC files loadable |

### Definition of Done
- [ ] OBD-II adapter auto-detected and configured
- [ ] SocketCAN interface (MCP2515) working with proper kernel modules
- [ ] Sensor fusion service running and producing fused positions
- [ ] Dead reckoning tested: 30s GPS blackout maintains < 50m position error
- [ ] CAN data visible in web UI dashboard
- [ ] Simulated CAN driver working for CI/CD testing

### Technical Notes

**Hardware Options:**

| Option | Interface | Cost | Data Access |
|--------|-----------|------|-------------|
| ELM327 USB/BT | OBD-II port | ~$15 | Standard PIDs only |
| MCP2515 + TJA1050 | SPI → CAN | ~$10 | Raw CAN frames |
| CANable / PCAN-USB | USB → CAN | ~$50-100 | Raw CAN frames |

**Supported OBD-II PIDs:**

| PID | Parameter | Use Case |
|-----|-----------|----------|
| 0x0D | Vehicle Speed | Dead reckoning primary input |
| 0x0C | Engine RPM | Vehicle state, logging |
| 0x2F | Fuel Level | Trip planning display |
| 0x05 | Coolant Temp | Vehicle health monitoring |

**Proprietary CAN Data (vehicle-specific DBC required):**

| Signal | Use Case |
|--------|----------|
| Steering Angle | Turn prediction for sensor fusion |
| Individual Wheel Speeds | Precise odometry, slip detection |
| Yaw Rate | Heading confirmation |
| Gear Position | Speed validation |

**Sensor Fusion Algorithm:**

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  GPS Fix    │────►│                  │────►│ Fused Position  │
│  (1-10 Hz)  │     │  Extended Kalman │     │  - lat/lon      │
└─────────────┘     │     Filter       │     │  - confidence   │
                    │                  │     │  - source type  │
┌─────────────┐     │  State Vector:   │     └─────────────────┘
│  CAN Data   │────►│  [lat, lon,      │
│  (10-50 Hz) │     │   vel_n, vel_e,  │
│  - speed    │     │   heading]       │
│  - steering │     └──────────────────┘
└─────────────┘
```

### Risks
| Risk | Mitigation |
|------|------------|
| Vehicle CAN compatibility varies | Support both OBD-II (universal) and SocketCAN (advanced) |
| Proprietary CAN data undocumented | DBC file support; community databases; fallback to OBD-II |
| CAN bus electrical isolation | Use isolated CAN transceiver; document wiring best practices |
| MCP2515 SPI performance on Pi | Use hardware SPI; tune interrupt handling; 500kbps sufficient |

---

## INFRA-E8: Documentation & Handoff

**Duration:** Weeks 12-14  
**Owner:** TBD  
**Priority:** Critical (DEL-004, DEL-005)

### Description
Create comprehensive documentation including: installation script (setup.sh) for existing Pi OS, hardware assembly guide, troubleshooting FAQ, system architecture diagrams, auto-generated API documentation (OpenAPI/Swagger), maintenance procedures (backup, restore, update, recovery), and final project report for academic handoff.

### User Stories

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| INFRA-8.1 | As a user, I need an installation script so I can install on existing Pi | 5 | setup.sh installs everything; tested on fresh Pi OS |
| INFRA-8.2 | As an operator, I need hardware setup documentation so I can assemble the system | 3 | HARDWARE.md covers all connections and wiring |
| INFRA-8.3 | As an operator, I need a troubleshooting guide so I can fix common issues | 5 | FAQ covers: no GPS, no WiFi, DB errors, boot failures |
| INFRA-8.4 | As a developer, I need architecture documentation so I understand the system | 3 | Updated architecture diagrams; component descriptions |
| INFRA-8.5 | As an operator, I need API documentation so I can integrate with the system | 3 | OpenAPI spec; Swagger UI available |
| INFRA-8.6 | As the instructor, I need a project summary so the work is captured | 5 | Final report: goals, implementation, lessons learned |
| INFRA-8.7 | As the next maintainer, I need maintenance procedures documented | 3 | Backup, restore, update, and recovery procedures |

### Definition of Done
- [ ] Installation script tested on fresh Raspberry Pi OS
- [ ] All documentation reviewed and complete
- [ ] API documentation auto-generated and accessible
- [ ] Troubleshooting guide covers top 10 issues
- [ ] Final project report submitted

### Risks
| Risk | Mitigation |
|------|------------|
| Documentation falling behind development | Allocate documentation time each sprint |
| Installation script breaking with OS updates | Pin Pi OS version; test against latest |

---

## Timeline Summary

```
Week:  1   2   3   4   5   6   7   8   9  10  11  12  13  14
       ├───┴───┼───┴───┼───┴───┼───┴───┼───┴───┼───┴───┼───┴───┤
E1:    ████████                                            Dev Environment
E2:        ████████████                                    Database
E3:                ████████████                            System Services
E4:                    ████████████                        Networking
E5:                        ████████████                    Offline Maps
E6:                                ████████████████        SD Card Image
E7:                                    ████████████        Monitoring
E8:                                            ████████████ Documentation
E9:                    ████████████                        CAN Bus/Fusion
```

---

## Dependencies Between Epics

```
INFRA-E1 ─────┬──────────────────────────────► INFRA-E6
              │
              ├─► INFRA-E2 ───┬───────────────► INFRA-E6
              │               │
              │               └─► INFRA-E5 ───► INFRA-E6
              │
              └─► INFRA-E3 ───┬─► INFRA-E4 ──► INFRA-E6
                              │
                              ├─► INFRA-E7 ──► INFRA-E8
                              │
                              └─► INFRA-E9 ──► INFRA-E6
                                   (CAN Bus)

All Epics ──────────────────────────────────► INFRA-E8
```

---

## Resource Requirements

| Resource | Quantity | Purpose |
|----------|----------|---------|
| Raspberry Pi 4 (4GB+) | 2 | Dev/test devices |
| High-endurance microSD (64GB+) | 4 | Testing image builds |
| USB GPS Module | 1 | GPS testing |
| RTL-SDR Dongle | 1 | APRS testing |
| ELM327 OBD-II Adapter (USB) | 1 | OBD-II CAN testing |
| MCP2515 CAN Module | 1 | SocketCAN testing (optional) |
| OBD-II Y-Splitter Cable | 1 | Allow simultaneous connections |
| GitHub Actions Minutes | ~500/month | CI/CD |
| External Monitor + Keyboard | 1 set | Hardware debugging |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Boot-to-operational time | < 60 seconds | Stopwatch test |
| GitHub Actions build success rate | > 95% | CI metrics |
| SD card image boot success | 100% first-try | Test on 3 different Pi 4s |
| Documentation coverage | 100% of features | Checklist review |
| Mean time to recovery (crash) | < 30 seconds | Watchdog test |

---

## Appendix: Story Point Reference

| Points | Complexity | Example |
|--------|------------|---------|
| 1 | Trivial | Config file change |
| 2 | Simple | Add udev rule |
| 3 | Moderate | Configure a service |
| 5 | Complex | Design new subsystem |
| 8 | Very Complex | Build automation pipeline |
| 13 | Epic-level | Should be broken down |
