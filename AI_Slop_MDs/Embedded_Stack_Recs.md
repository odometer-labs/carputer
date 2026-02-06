# Embedded Team Tech Stack Recommendations

## Overview
This document outlines the recommended technology stack for the Embedded Team responsible for GPS hardware integration, APRS reception, and display configuration for the Raspberry Pi GPS Tracking Carputer project.

---

## Core GPS Stack

### GPS Daemon Layer
- **gpsd** (v3.25+)
  - Universal GPS interface daemon
  - Supports virtually all GPS modules (USB, UART, I2C)
  - Provides unified interface regardless of underlying hardware
  - Handles NMEA sentence parsing automatically
  - Built-in client libraries for Python, C, C++

### Client Libraries
- **gpsd-py3** or **gps3** - Python bindings for gpsd
- **python-gps** - Alternative Python library
- Direct socket connection to gpsd (JSON over TCP port 2947)

---

## APRS/RTL-SDR Stack

### Radio Reception
- **RTL-SDR drivers** (rtl-sdr package)
- **Direwolf** (v1.7+) - Software TNC (Terminal Node Controller)
  - Decodes APRS packets from audio
  - Can interface with RTL-SDR via virtual audio cables
- **rtl_fm** - Command-line FM demodulator for RTL-SDR

### Audio Routing
- **PulseAudio** or **pipewire** - Audio routing between RTL-SDR and Direwolf
- **sox** - Audio format conversion if needed

### APRS Parsing
- **aprslib** (Python) - Parse APRS packets into structured data
- Direct integration with Direwolf's KISS interface

---

## System Integration

### Programming Languages
- **Python 3.11+** - Primary language for GPS/APRS data pipelines
- **Bash** - System configuration and service management
- **C/C++** (optional) - Performance-critical components or direct hardware access

### Process Management
- **systemd** - Service management for all daemons
  - `gpsd.service`
  - `direwolf.service`
  - Custom tracking service
- **watchdog** - Hardware watchdog integration for crash recovery

### Configuration Management
- **Python configparser** or **YAML** (with PyYAML)
- `/etc/default/` files for system service configuration

---

## Hardware Interfaces

### GPIO (if needed)
- **RPi.GPIO** or **gpiozero** (Python) - GPIO pins for GPS or control signals
- **pigpio** - Advanced GPIO control with precise timing

### Display
- **X11** or **Wayland** - Display server for touch interface
- **Chromium (kiosk mode)** - If frontend is web-based, run full-screen browser
- **Qt/PyQt5** or **Kivy** - If building native touch application

---

## Hardware-Specific Considerations

### Common GPS Module Categories

#### 1. USB GPS Dongles (Most Common)
**Examples:** GlobalSat BU-353, VK-162, U-blox NEO-6M/7M/8M with USB

- **Works with:** gpsd automatically detects as `/dev/ttyUSB0` or `/dev/ttyACM0`
- **No special drivers needed** - plug and play
- **Power:** Usually bus-powered, no external power needed

#### 2. UART/Serial GPS Modules
**Examples:** Adafruit Ultimate GPS, U-blox modules on GPIO

- **Works with:** gpsd on `/dev/ttyAMA0` or `/dev/serial0`
- **Requires:** Disabling serial console in `/boot/config.txt`
- **Wiring:** Direct connection to GPIO pins (TX, RX, VCC, GND)

#### 3. I2C GPS Modules
**Examples:** SparkFun I2C GPS modules

- **Works with:** Custom Python scripts using smbus2
- **Less common:** May not work directly with gpsd
- **More complex:** Requires manual NMEA parsing

#### 4. HAT-Based GPS Modules
**Examples:** Adafruit Ultimate GPS HAT, Waveshare GPS/GNSS HAT

- **Works with:** Usually UART-based, pre-configured for Pi
- **Advantage:** Clean mounting, integrated antenna options
- **gpsd compatible:** Yes, with proper device path configuration

---

## Recommended Tech Stack Options

### Option A: USB GPS Module
```
Hardware: GlobalSat BU-353, VK-162, etc.
├── gpsd (auto-detects on /dev/ttyUSB0)
├── Python app using gpsd-py3
└── No special configuration needed
```

### Option B: UART GPS Module (GPIO)
```
Hardware: U-blox NEO-6M on GPIO pins
├── Disable console: /boot/cmdline.txt
├── Enable UART: /boot/config.txt
├── gpsd on /dev/serial0
└── Python app using gpsd-py3
```

### Option C: GPS HAT
```
Hardware: Adafruit Ultimate GPS HAT
├── Pre-wired to GPIO serial
├── gpsd on /dev/ttyAMA0
├── Includes RTC (bonus!)
└── Python app using gpsd-py3
```

---

## Default Assumption: USB GPS + RTL-SDR Dongle

### Full Stack Architecture
```
OS: Raspberry Pi OS Lite (64-bit)
├── System Services
│   ├── gpsd (GPS daemon)
│   ├── direwolf (APRS decoder)
│   └── rtl_fm (SDR demodulator)
├── Data Pipeline (Python 3.11+)
│   ├── gpsd-py3 (GPS client)
│   ├── aprslib (APRS parsing)
│   ├── psycopg2 (PostgreSQL driver)
│   ├── requests (API communication)
│   └── systemd service wrapper
├── Configuration
│   ├── /etc/default/gpsd
│   ├── /etc/direwolf.conf
│   └── Custom YAML config
└── Monitoring
    ├── Python logging module
    └── systemd journal integration
```

---

## Key Questions for Hardware Selection

1. **Do you already have GPS hardware?** If so, what model?
2. **USB vs GPIO preference?** USB is simpler, GPIO is cleaner for permanent install
3. **Do you have the RTL-SDR dongle yet?** (Any RTL2832U-based dongle works)
4. **Touch display model?** (Official Pi Touch Display vs HDMI touchscreen)
5. **Permanent vs portable installation?** Affects power and mounting decisions

---

## Notes

- **gpsd abstracts most GPS hardware differences** - The stack is largely hardware-agnostic
- **RTL-SDR compatibility** - Any RTL2832U-based dongle works (no license required for reception)
- **Flexibility** - This stack can be adapted once specific hardware is selected
- **Testing recommended** - Verify GPS lock and APRS reception before vehicle installation

---

## Next Steps

1. Identify specific GPS module and RTL-SDR hardware
2. Configure gpsd and Direwolf for hardware
3. Develop Python data pipeline services
4. Create systemd service definitions
5. Test GPS accuracy and APRS reception
6. Integrate with backend PostgreSQL database
