# gpsd JSON Protocol Reference
**Source:** `gpsd_json(5)` man page (gpsd 3.22), verified against live daemon output  
**Target audience:** Backend engineers writing data models and GPS ingestion services  
**Transport:** TCP socket, `localhost:2947` (IPv4 or IPv6)  
**Serialization:** JSON (RFC 7159), newline-delimited (`\r\n` terminated), max 1536 bytes per message

---

## Table of Contents

1. [Protocol Overview](#1-protocol-overview)
2. [Connection Lifecycle](#2-connection-lifecycle)
3. [WATCH Command](#3-watch-command)
4. [Message Class Index](#4-message-class-index)
5. [TPV — Time Position Velocity](#5-tpv--time-position-velocity)
6. [SKY — Satellite Sky View](#6-sky--satellite-sky-view)
7. [GST — Pseudorange Noise](#7-gst--pseudorange-noise)
8. [ATT — Vehicle Attitude](#8-att--vehicle-attitude)
9. [TOFF — Serial Timing Offset](#9-toff--serial-timing-offset)
10. [PPS — Pulse Per Second](#10-pps--pulse-per-second)
11. [OSC — Disciplined Oscillator](#11-osc--disciplined-oscillator)
12. [VERSION](#12-version)
13. [DEVICES / DEVICE](#13-devices--device)
14. [POLL](#14-poll)
15. [ERROR](#15-error)
16. [Client Library Interfaces](#16-client-library-interfaces)
17. [Data Modeling Notes](#17-data-modeling-notes)
18. [Field Quick-Reference](#18-field-quick-reference)

---

## 1. Protocol Overview

```
Client                          gpsd daemon
  |                                  |
  |-------- TCP connect :2947 ------>|
  |<------- {"class":"VERSION",...} -|   (sent immediately on connect)
  |<------- {"class":"DEVICES",...} -|   (sent immediately on connect)
  |                                  |
  |--- ?WATCH={"enable":true,        |
  |            "json":true,          |
  |            "pps":true};  ------->|
  |<------- {"class":"WATCH",...}  --|   (echo of policy)
  |<------- {"class":"DEVICES",...} -|
  |                                  |
  |<------- {"class":"TPV",...}\r\n -|   ~1 Hz
  |<------- {"class":"SKY",...}\r\n -|   ~1 Hz
  |<------- {"class":"TOFF",...}\r\n-|   ~1 Hz (if pps:true)
  |<------- {"class":"PPS",...}\r\n -|   on each PPS pulse (if pps:true)
  |                  ...             |
```

**Key protocol rules:**
- Every request line starts with `?` and ends with `;` or newline
- Request lines are ASCII only, max 80 characters
- Responses are JSON objects, one per line, `\r\n` terminated
- `null` values are **never** present — absent fields are simply omitted
- The `"class"` attribute is always the first field and is the message discriminator
- Truncation at 1536 bytes is possible — client code must handle invalid JSON fragments
- Field order within an object is not significant except: parent fields are emitted before dependent optional children

---

## 2. Connection Lifecycle

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 2947))

# Receive VERSION and DEVICES automatically
buf = b""
# ... read until two \r\n terminated objects received

# Activate streaming
sock.sendall(b'?WATCH={"enable":true,"json":true,"pps":true};\r\n')

# Read loop
for line in sock.makefile():
    obj = json.loads(line.strip())
    dispatch(obj["class"], obj)
```

Using the library is always preferred over raw sockets — see [Section 16](#16-client-library-interfaces).

---

## 3. WATCH Command

Sent once after connect to activate the stream. Without this, the daemon sends nothing.

```
?WATCH={"enable":true,"json":true,"pps":true};
```

### WATCH Object Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `class` | string | — | Always `"WATCH"` in response |
| `enable` | boolean | `true` | Enable (`true`) or disable (`false`) watcher mode |
| `json` | boolean | `false` | Enable JSON report output. **Must be `true` to receive TPV/SKY/etc.** |
| `nmea` | boolean | `false` | Also emit binary packets as pseudo-NMEA |
| `raw` | integer | — | `1` = raw NMEA/AIVDM stream (binary hex-dumped); `2` = verbatim binary |
| `scaled` | boolean | `false` | Apply scaling divisors before output |
| `split24` | boolean | `false` | AIS type24 aggregation; irrelevant for GPS-only deployments |
| `pps` | boolean | `false` | **Enable TOFF and PPS messages.** Required to receive timing reports |
| `device` | string | — | Watch only the specified device path instead of all devices |
| `remote` | string | — | URL of remote daemon (response only) |

**For a carputer GPS backend, the minimum correct invocation is:**
```
?WATCH={"enable":true,"json":true};
```
**To also receive timing data (TOFF/PPS):**
```
?WATCH={"enable":true,"json":true,"pps":true};
```

---

## 4. Message Class Index

| Class | Direction | Frequency | Description |
|-------|-----------|-----------|-------------|
| `VERSION` | server→client | Once on connect | Daemon version and protocol level |
| `DEVICES` | server→client | On connect + device events | List of active devices |
| `DEVICE` | server→client | On device change | Single device state update |
| `WATCH` | both | On `?WATCH` command | Policy echo |
| `TPV` | server→client | ~1 Hz | **Time-Position-Velocity — primary data** |
| `SKY` | server→client | ~1 Hz | Satellite positions and signal quality |
| `GST` | server→client | ~1 Hz (if available) | Pseudorange noise / error ellipse |
| `ATT` | server→client | Device-dependent | Vehicle attitude (compass/IMU) |
| `TOFF` | server→client | ~1 Hz (requires `pps:true`) | Serial-stream timing offset |
| `PPS` | server→client | Once per second (requires `pps:true` + hardware PPS) | Hardware pulse timing |
| `OSC` | server→client | On change | GPS-disciplined oscillator status |
| `POLL` | both | On `?POLL` command | Snapshot of last-seen fixes |
| `ERROR` | server→client | On error | Error description string |

---

## 5. TPV — Time Position Velocity

The primary message for location data. Emitted approximately once per second per device. **Multiple TPV objects may be sent per epoch** if the receiver dribbles data incrementally.

**`class` and `mode` are always present. All other fields are optional** — their presence depends on what the receiver reported and what gpsd could calculate.

### Mode Values

| Value | Meaning |
|-------|---------|
| `0` | No mode value yet seen |
| `1` | No fix |
| `2` | 2D fix (lat/lon, no altitude) |
| `3` | 3D fix (lat/lon + altitude) |

### Status Values (optional adjective modifier to mode)

> `status` is a fix-quality qualifier, not a replacement for `mode`. Many receivers do not supply it. Values `0` and `1` are never emitted in JSON output.

| Value | Meaning |
|-------|---------|
| `2` | DGPS fix |
| `3` | RTK Fixed point |
| `4` | RTK Floating point |
| `5` | DR (dead reckoning) fix |
| `6` | GNSS + DR fix |
| `7` | Time (surveyed) fix |
| `8` | Simulated |
| `9` | P(Y) fix |

### TPV Field Table

| Field | Always? | Type | Units | Description |
|-------|---------|------|-------|-------------|
| `class` | **Yes** | string | — | Fixed: `"TPV"` |
| `device` | No | string | — | Originating device path (e.g. `/dev/ttyACM0`) |
| `mode` | **Yes** | integer | — | NMEA mode. See table above. Emitted before optional fields |
| `status` | No | integer | — | Fix quality. See table above. Never 0 or 1 in output |
| `time` | No | string | ISO8601 UTC | Timestamp. Up to `.001s` precision. Absent if mode < 2 |
| `ept` | No | float | seconds | Estimated timestamp error. Certainty unknown |
| `lat` | No | float | degrees | Latitude. Positive = North, negative = South |
| `lon` | No | float | degrees | Longitude. Positive = East, negative = West |
| `altHAE` | No | float | meters | Altitude above ellipsoid (WGS84). Preferred altitude field |
| `altMSL` | No | float | meters | Altitude above Mean Sea Level. `altMSL = altHAE - geoidSep`. Geoid is rarely well-specified |
| `alt` | No | float | meters | **Deprecated. Undefined. Do not use.** Use `altHAE` or `altMSL` |
| `geoidSep` | No | float | meters | Geoid separation: WGS84 ellipsoid minus geoid (MSL). gpsd interpolates from EGM2008 if receiver omits it (usually ±1m, up to ±12m error) |
| `climb` | No | float | m/s | Vertical velocity. Positive = ascending, negative = descending |
| `speed` | No | float | m/s | Speed over ground |
| `track` | No | float | degrees | Course over ground, true north |
| `magtrack` | No | float | degrees | Course over ground, magnetic north |
| `magvar` | No | float | degrees | Magnetic variation. **Positive = West, Negative = East** |
| `datum` | No | string | — | Current datum. Ideally `"WGS84"` |
| `depth` | No | float | meters | Depth below keel (marine use) |
| `leapseconds` | No | integer | seconds | Current GPS-UTC leap seconds |
| `dgpsAge` | No | float | seconds | Age of DGPS corrections |
| `dgpsSta` | No | integer | — | DGPS station ID |
| `sep` | No | float | meters | Estimated Spherical (3D) Position Error ~95% confidence |
| `eph` | No | float | meters | Estimated horizontal (2D) position error. Also known as EPE. Certainty unknown |
| `epv` | No | float | meters | Estimated vertical error. Certainty unknown |
| `epx` | No | float | meters | Longitude error estimate. Certainty unknown |
| `epy` | No | float | meters | Latitude error estimate. Certainty unknown |
| `ept` | No | float | seconds | Estimated timestamp error. Certainty unknown |
| `eps` | No | float | m/s | Estimated speed error. Certainty unknown |
| `epc` | No | float | m/s | Estimated climb error. Certainty unknown |
| `epd` | No | float | degrees | Estimated track (direction) error. Certainty unknown |
| `relN` | No | float | meters | RTK: North component of baseline vector to base station |
| `relE` | No | float | meters | RTK: East component of baseline vector |
| `relD` | No | float | meters | RTK: Down component of baseline vector |
| `velN` | No | float | m/s | NED North velocity component |
| `velE` | No | float | m/s | NED East velocity component |
| `velD` | No | float | m/s | NED Down velocity component |
| `ecefx` | No | float | meters | ECEF X position |
| `ecefy` | No | float | meters | ECEF Y position |
| `ecefz` | No | float | meters | ECEF Z position |
| `ecefpAcc` | No | float | meters | ECEF position error. Certainty unknown |
| `ecefvx` | No | float | m/s | ECEF X velocity |
| `ecefvy` | No | float | m/s | ECEF Y velocity |
| `ecefvz` | No | float | m/s | ECEF Z velocity |
| `ecefvAcc` | No | float | m/s | ECEF velocity error. Certainty unknown |
| `wanglem` | No | float | degrees | Wind angle, magnetic |
| `wangler` | No | float | degrees | Wind angle, relative |
| `wanglet` | No | float | degrees | Wind angle, true |
| `wspeedr` | No | float | m/s | Wind speed, relative |
| `wspeedt` | No | float | m/s | Wind speed, true |

### TPV Example (3D fix, RTK Float)

```json
{
  "class":   "TPV",
  "device":  "/dev/ttyACM0",
  "mode":    3,
  "status":  4,
  "time":    "2026-02-25T03:49:53.000Z",
  "ept":     0.005,
  "lat":     45.523064000,
  "lon":     -122.676483000,
  "altHAE":  52.347,
  "altMSL":  45.121,
  "geoidSep": 7.226,
  "speed":   0.012,
  "track":   270.500,
  "climb":   0.000,
  "eph":     0.420,
  "epv":     0.810,
  "sep":     0.920
}
```

### RTK State Summary (ZED-F9P specific)

| `mode` | `status` | `eph` typical | Interpretation |
|--------|----------|---------------|----------------|
| 1 | absent | — | No fix. Acquiring satellites |
| 2 | absent | ~3–8m | 2D GNSS fix |
| 3 | absent | ~1–5m | 3D GNSS fix |
| 3 | 2 | ~0.5–2m | DGPS-corrected fix |
| 3 | 4 | ~0.05–0.5m | RTK Float — converging |
| 3 | 3 | ~0.01–0.05m | RTK Fixed — centimeter accuracy |

---

## 6. SKY — Satellite Sky View

Reports satellite positions and signal quality. Emitted approximately once per second.

### SKY Object Fields

| Field | Always? | Type | Description |
|-------|---------|------|-------------|
| `class` | **Yes** | string | Fixed: `"SKY"` |
| `device` | No | string | Originating device path |
| `time` | No | string | ISO8601 UTC timestamp, up to `.001s` precision |
| `gdop` | No | float | Geometric (hyperspherical) DOP — combines PDOP and TDOP |
| `hdop` | No | float | Horizontal DOP |
| `pdop` | No | float | Position (3D spherical) DOP |
| `tdop` | No | float | Time DOP |
| `vdop` | No | float | Vertical (altitude) DOP |
| `xdop` | No | float | Longitudinal DOP (along-track) |
| `ydop` | No | float | Latitudinal DOP (cross-track) |
| `nSat` | No | integer | Total satellite objects in `satellites` array |
| `uSat` | No | integer | Satellites used in the navigation solution |
| `satellites` | **Yes** | array | List of satellite objects (may be empty array) |

> gpsd always passes through whatever DOPs the device reports, then attempts to fill in others by computing covariance matrix determinants from the satellite view. DOPs may be absent if determinants are singular.

### Satellite Object Fields

Satellite objects exist only inside a `satellites` array — they never have a `"class"` field.

| Field | Always? | Type | Description |
|-------|---------|------|-------------|
| `PRN` | **Yes** | integer | PRN ID. 1–63: GNSS satellites; 64–96: GLONASS; 100–164: SBAS |
| `used` | **Yes** | boolean | Used in current navigation solution |
| `az` | No | integer | Azimuth, degrees from true north (0–359) |
| `el` | No | integer | Elevation, degrees above horizon (0–90) |
| `ss` | No | integer | Signal-to-noise ratio, dBHz |
| `gnssid` | No | integer | GNSS system ID (u-blox definition, not NMEA): `0`=GPS, `2`=Galileo, `3`=BeiDou, `5`=QZSS, `6`=GLONASS |
| `svid` | No | integer | Satellite ID within its constellation (u-blox definition) |
| `sigid` | No | integer | Signal ID (u-blox definition — see u-blox protocol spec for encoding) |
| `freqid` | No | integer | GLONASS frequency slot + 7, range 0–13. GLONASS satellites only |
| `health` | No | integer | `0`=unknown, `1`=healthy, `2`=unhealthy |

### SKY Example

```json
{
  "class": "SKY",
  "device": "/dev/ttyACM0",
  "time": "2026-02-25T03:49:53.000Z",
  "hdop": 1.24,
  "pdop": 1.99,
  "xdop": 1.55,
  "vdop": 1.58,
  "nSat": 18,
  "uSat": 10,
  "satellites": [
    {"PRN": 8,  "el": 66, "az": 189, "ss": 44, "used": true,  "gnssid": 0, "svid": 8,  "health": 1},
    {"PRN": 10, "el": 51, "az": 304, "ss": 29, "used": true,  "gnssid": 0, "svid": 10, "health": 1},
    {"PRN": 23, "el": 6,  "az": 84,  "ss": 0,  "used": false, "gnssid": 0, "svid": 23, "health": 1},
    {"PRN": 72, "el": 38, "az": 120, "ss": 35, "used": true,  "gnssid": 6, "svid": 8,  "health": 1}
  ]
}
```

---

## 7. GST — Pseudorange Noise

Reports pseudorange noise statistics. Provides the error ellipse — more precise than the `ep*` fields in TPV. The ZED-F9P produces this message.

| Field | Always? | Type | Units | Description |
|-------|---------|------|-------|-------------|
| `class` | **Yes** | string | — | Fixed: `"GST"` |
| `device` | No | string | — | Originating device path |
| `time` | No | string | ISO8601 UTC | Timestamp |
| `rms` | No | float | — | Standard deviation of range inputs to navigation process (pseudoranges + DGPS corrections) |
| `major` | No | float | meters | Standard deviation of semi-major axis of error ellipse |
| `minor` | No | float | meters | Standard deviation of semi-minor axis of error ellipse |
| `orient` | No | float | degrees | Orientation of semi-major axis, degrees from true north |
| `lat` | No | float | meters | Standard deviation of latitude error |
| `lon` | No | float | meters | Standard deviation of longitude error |
| `alt` | No | float | meters | Standard deviation of altitude error |

### GST Example

```json
{
  "class":  "GST",
  "device": "/dev/ttyACM0",
  "time":   "2026-02-25T03:49:53.000Z",
  "rms":    0.024,
  "major":  0.018,
  "minor":  0.011,
  "orient": 52.400,
  "lat":    0.016,
  "lon":    0.012,
  "alt":    0.031
}
```

---

## 8. ATT — Vehicle Attitude

Returned by digital compass and gyroscope sensors. May include heading, pitch, roll, yaw, magnetic field, acceleration, gyroscope readings, and water depth if bundled in a marine navigation system. `"class"` and `"device"` are always present.

| Field | Always? | Type | Units | Description |
|-------|---------|------|-------|-------------|
| `class` | **Yes** | string | — | Fixed: `"ATT"` |
| `device` | **Yes** | string | — | Originating device path |
| `time` | No | string | ISO8601 UTC | Timestamp |
| `heading` | No | float | degrees | Heading from true north |
| `mag_st` | No | string | — | Magnetometer status code (see below) |
| `pitch` | No | float | degrees | Pitch |
| `pitch_st` | No | string | — | Pitch sensor status code |
| `yaw` | No | float | degrees | Yaw |
| `yaw_st` | No | string | — | Yaw sensor status code |
| `roll` | No | float | degrees | Roll |
| `roll_st` | No | string | — | Roll sensor status code |
| `dip` | No | float | degrees | Magnetic inclination. Positive = field points downward into Earth |
| `mag_len` | No | float | — | Scalar magnetic field strength |
| `mag_x` | No | float | — | Magnetic field X component |
| `mag_y` | No | float | — | Magnetic field Y component |
| `mag_z` | No | float | — | Magnetic field Z component |
| `acc_len` | No | float | — | Scalar acceleration |
| `acc_x` | No | float | — | Acceleration X component |
| `acc_y` | No | float | — | Acceleration Y component |
| `acc_z` | No | float | — | Acceleration Z component |
| `gyro_x` | No | float | — | Gyroscope X component |
| `gyro_y` | No | float | — | Gyroscope Y component |
| `depth` | No | float | meters | Water depth |
| `temp` | No | float | °C | Sensor temperature |

### Sensor Status Codes (TNT Revolution digital compasses)

| Code | Meaning |
|------|---------|
| `C` | Magnetometer calibration alarm |
| `L` | Low alarm |
| `M` | Low warning |
| `N` | Normal |
| `O` | High warning |
| `P` | High alarm |
| `V` | Magnetometer voltage level alarm |

---

## 9. TOFF — Serial Timing Offset

Emitted once per cycle. Reports the offset between GPS serial-stream time and the host system clock. Distinct from PPS: TOFF derives time from the serial data stream; PPS derives time from the hardware pulse.

**Requires `"pps":true` in the WATCH command.**

Serial timing has significantly more jitter than PPS — serial interrupt latency plus GPS computation time can add 10ms–700ms offset with 100–300ms combined jitter. Use PPS for precision timekeeping; use TOFF as a fallback or sanity check.

| Field | Always? | Type | Description |
|-------|---------|------|-------------|
| `class` | **Yes** | string | Fixed: `"TOFF"` |
| `device` | **Yes** | string | Originating device path |
| `real_sec` | **Yes** | integer | GPS time, whole seconds |
| `real_nsec` | **Yes** | integer | GPS time, nanosecond part |
| `clock_sec` | **Yes** | integer | System clock time, whole seconds |
| `clock_nsec` | **Yes** | integer | System clock time, nanosecond part |

> `precision` is absent from TOFF (assumed -2). It is present in PPS.

### TOFF Example

```json
{
  "class":      "TOFF",
  "device":     "/dev/ttyACM0",
  "real_sec":   1771991393,
  "real_nsec":  0,
  "clock_sec":  1771991393,
  "clock_nsec": 412847
}
```

---

## 10. PPS — Pulse Per Second

Emitted each time the daemon receives a valid PPS strobe from a hardware device. Reports GPS time at the rising edge of the pulse versus system clock at that same moment.

**Requires `"pps":true` in the WATCH command, and a hardware PPS connection** (TIMEPULSE pin from ZED-F9P to a GPIO configured as `/dev/pps0`).

PPS via real serial-line strobe: serial interrupt latency bounded above by ~10µs, reducible to <1µs with RFC 2783 kernel PPS API. USB-serial emulation is limited to ~1ms.

| Field | Always? | Type | Description |
|-------|---------|------|-------------|
| `class` | **Yes** | string | Fixed: `"PPS"` |
| `device` | **Yes** | string | Originating device path |
| `real_sec` | **Yes** | integer | GPS time at PPS edge, whole seconds |
| `real_nsec` | **Yes** | integer | GPS time at PPS edge, nanosecond part |
| `clock_sec` | **Yes** | integer | System clock at PPS edge, whole seconds |
| `clock_nsec` | **Yes** | integer | System clock at PPS edge, nanosecond part |
| `precision` | **Yes** | integer | NTP-style precision estimate (log₂ seconds, e.g. `-20` ≈ 1µs) |
| `qErr` | No | integer | Quantization error in picoseconds. Also known as sawtooth error |

### PPS Example

```json
{
  "class":      "PPS",
  "device":     "/dev/ttyACM0",
  "real_sec":   1771991393,
  "real_nsec":  0,
  "clock_sec":  1771991393,
  "clock_nsec": 8241,
  "precision":  -20
}
```

---

## 11. OSC — Disciplined Oscillator

Reports the status of a GPS-disciplined oscillator (GPSDO). Not produced by the ZED-F9P directly — relevant only if a GPSDO is attached.

| Field | Always? | Type | Description |
|-------|---------|------|-------------|
| `class` | **Yes** | string | Fixed: `"OSC"` |
| `device` | **Yes** | string | Originating device path |
| `running` | **Yes** | boolean | Oscillator is currently running |
| `reference` | **Yes** | boolean | Receiving a GPS PPS signal |
| `disciplined` | **Yes** | boolean | PPS is stable and disciplining the oscillator |
| `delta` | **Yes** | integer (ns) | Time difference between GPSDO PPS output and GPS PPS input |

---

## 12. VERSION

Sent automatically to every client on connect, before any other message.

| Field | Always? | Type | Description |
|-------|---------|------|-------------|
| `class` | **Yes** | string | Fixed: `"VERSION"` |
| `release` | **Yes** | string | Public release level (e.g. `"3.22"`) |
| `rev` | **Yes** | string | Internal revision control hash |
| `proto_major` | **Yes** | integer | Protocol major version |
| `proto_minor` | **Yes** | integer | Protocol minor version |
| `remote` | No | string | URL of remote daemon. Empty = local daemon |

### Example

```json
{
  "class":       "VERSION",
  "release":     "3.22",
  "rev":         "3.22",
  "proto_major": 3,
  "proto_minor": 15
}
```

---

## 13. DEVICES / DEVICE

`DEVICES` is sent automatically on connect and on device change events. A bare `DEVICE` may also be sent without a `DEVICES` wrapper when a single device changes state.

### DEVICES Object

| Field | Always? | Type | Description |
|-------|---------|------|-------------|
| `class` | **Yes** | string | Fixed: `"DEVICES"` |
| `devices` | **Yes** | array | List of DEVICE objects |
| `remote` | No | string | URL of remote daemon |

### DEVICE Object

| Field | Always? | Type | Description |
|-------|---------|------|-------------|
| `class` | **Yes** | string | Fixed: `"DEVICE"` |
| `path` | No | string | Device path. May be omitted if only one channel is subscribed |
| `activated` | No | string | ISO8601 timestamp when device was activated. Absent if inactive |
| `flags` | No | integer | Bit vector of packet types seen: GPS, RTCM2, RTCM3, AIS. Absent until identifiable packets seen |
| `driver` | No | string | gpsd driver name (e.g. `"u-blox"`, `"NMEA0183"`) |
| `subtype` | No | string | Driver subtype string |
| `bps` | No | integer | Current serial baud rate |
| `parity` | No | string | Serial parity: `"N"`, `"O"`, `"E"` |
| `stopbits` | No | integer | Stop bits: `1` or `2` |
| `native` | No | integer | `0` = NMEA mode, `1` = native/binary mode |
| `cycle` | No | float | Receiver update cycle, seconds |
| `mincycle` | No | float | Minimum supported cycle, seconds |

---

## 14. POLL

On-demand snapshot command. Requires prior `?WATCH` activation.

**Send:** `?POLL;`

| Field | Always? | Type | Description |
|-------|---------|------|-------------|
| `class` | **Yes** | string | Fixed: `"POLL"` |
| `time` | **Yes** | string | ISO8601 timestamp of poll |
| `active` | **Yes** | integer | Count of active devices |
| `tpv` | **Yes** | array | Last-seen TPV objects, one per active device |
| `sky` | **Yes** | array | Last-seen SKY objects, one per active device |

> **Warning:** If you poll while a device is mid-sentence (accumulating a fix from multiple NMEA sentences), the response contains only the fix data collected so far in the current epoch — potentially up to 1 cycle (~1 second) stale. Prefer the streaming `?WATCH` mode for real-time data.

---

## 15. ERROR

| Field | Always? | Type | Description |
|-------|---------|------|-------------|
| `class` | **Yes** | string | Fixed: `"ERROR"` |
| `message` | **Yes** | string | Human-readable error description |

---

## 16. Client Library Interfaces

### Python — `python3-gps`

Install: `sudo apt install python3-gps`

```python
import gps
import math

session = gps.gps(host="localhost", port=2947)
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

for report in session:
    msg_class = report.get("class")

    if msg_class == "TPV":
        mode = report.get("mode", 0)
        if mode < 2:
            continue  # no fix yet

        lat    = report.get("lat")
        lon    = report.get("lon")
        altHAE = report.get("altHAE")
        altMSL = report.get("altMSL")
        speed  = report.get("speed")
        track  = report.get("track")
        climb  = report.get("climb")
        eph    = report.get("eph")
        sep    = report.get("sep")
        status = report.get("status", 0)
        time   = report.get("time")

        # Always guard floats — absent fields return None, not NaN, from Python binding
        if lat is not None and lon is not None:
            process_fix(lat, lon, altMSL, speed, track, eph, status, time)

    elif msg_class == "SKY":
        hdop = report.get("hdop")
        nSat = report.get("nSat", 0)
        uSat = report.get("uSat", 0)
        sats = report.get("satellites", [])

    elif msg_class == "GST":
        lat_err = report.get("lat")   # 1-sigma latitude error in meters
        lon_err = report.get("lon")   # 1-sigma longitude error in meters
        alt_err = report.get("alt")
```

**Notes:**
- `gps.WATCH_NEWSTYLE` enables JSON protocol
- `session` is iterable; each iteration blocks on `session.read()`
- `report` is a dict-like object — use `.get()` with defaults throughout
- Run in a thread or async task in your backend; the iterator blocks

### C — `libgps`

Install: `sudo apt install libgps-dev`  
Compile: `gcc -o gps_consumer gps_consumer.c -lgps -lm`

```c
#include <gps.h>
#include <math.h>
#include <errno.h>

int main(void) {
    struct gps_data_t gps_data;

    if (gps_open("localhost", "2947", &gps_data) != 0) {
        fprintf(stderr, "gps_open() failed: %s\n", gps_errstr(errno));
        return 1;
    }

    gps_stream(&gps_data, WATCH_ENABLE | WATCH_JSON, NULL);

    while (1) {
        if (!gps_waiting(&gps_data, 5000000)) {  /* 5s timeout in microseconds */
            continue;
        }

        if (gps_read(&gps_data, NULL, 0) == -1) {
            break;  /* daemon disconnected */
        }

        /* Always check set bitmask before reading fields */
        if (gps_data.set & MODE_SET) {
            int mode = gps_data.fix.mode;

            if (mode >= MODE_2D && (gps_data.set & LATLON_SET)) {
                double lat = gps_data.fix.latitude;
                double lon = gps_data.fix.longitude;

                if (isfinite(lat) && isfinite(lon)) {
                    /* safe to use */
                }
            }

            if (mode == MODE_3D && (gps_data.set & ALTITUDE_SET)) {
                double altHAE = gps_data.fix.altHAE;
                double altMSL = gps_data.fix.altMSL;
                if (isfinite(altHAE)) { /* use */ }
            }
        }

        if (gps_data.set & SPEED_SET) {
            double speed = gps_data.fix.speed;
            if (isfinite(speed)) { /* use */ }
        }

        if (gps_data.set & TRACK_SET) {
            double track = gps_data.fix.track;
            if (isfinite(track)) { /* use */ }
        }

        if (gps_data.set & DOP_SET) {
            double hdop = gps_data.dop.hdop;
            if (isfinite(hdop)) { /* use */ }
        }
    }

    gps_stream(&gps_data, WATCH_DISABLE, NULL);
    gps_close(&gps_data);
    return 0;
}
```

### Key `set` Bitmask Flags (gps.h)

| Flag | Meaning |
|------|---------|
| `TIME_SET` | `fix.time` is valid |
| `LATLON_SET` | `fix.latitude` and `fix.longitude` are valid |
| `ALTITUDE_SET` | `fix.altHAE` and `fix.altMSL` are valid |
| `SPEED_SET` | `fix.speed` is valid |
| `TRACK_SET` | `fix.track` is valid |
| `CLIMB_SET` | `fix.climb` is valid |
| `MODE_SET` | `fix.mode` is valid |
| `DOP_SET` | `dop.*` fields are valid |
| `SATELLITE_SET` | `satellites[]` array is valid |

> **Critical:** Invalid or unknown floating-point values are set to `NAN` in the C struct. **Always call `isfinite()` before using any float from `gps_data_t`.** Never assume a field is valid because `gps_read()` returned — check the bitmask.

### Raw Socket / Language-Agnostic

For Rust, Go, or any language without a gpsd binding:

```
1. TCP connect to localhost:2947
2. Read until \r\n twice (VERSION + DEVICES)
3. Write: ?WATCH={"enable":true,"json":true,"pps":true};\r\n
4. Read loop: split on \r\n, parse each line as JSON
5. Dispatch on obj["class"]
6. Handle truncation: catch JSON parse errors, discard partial objects
```

---

## 17. Data Modeling Notes

### Minimal GPS Fix Model

```python
@dataclass
class GPSFix:
    # Always present with valid fix
    mode: int                    # 2 or 3
    timestamp: datetime          # parsed from time field

    # Present with 2D+ fix
    lat: float                   # degrees, WGS84
    lon: float                   # degrees, WGS84

    # Present with 3D fix
    alt_hae: Optional[float]     # meters above ellipsoid
    alt_msl: Optional[float]     # meters above MSL

    # Quality
    status: Optional[int]        # fix type; 3=RTK Fixed, 4=RTK Float
    eph: Optional[float]         # horizontal error estimate, meters
    sep: Optional[float]         # 3D spherical error estimate, meters

    # Kinematics
    speed: Optional[float]       # m/s
    track: Optional[float]       # degrees true north
    climb: Optional[float]       # m/s

    # Source
    device: Optional[str]        # e.g. /dev/ttyACM0
```

### Handling Optional Fields

Every field except `class` and `mode` (for TPV) and `class` and `used`/`PRN` (for satellite objects) is optional. The correct pattern is always:

```python
# Python
lat = report.get("lat")
if lat is None:
    return  # no fix data yet

# C
if (!isfinite(gps_data.fix.latitude)) return;
if (!(gps_data.set & LATLON_SET)) return;
```

### `alt` vs `altHAE` vs `altMSL`

- **`alt` is deprecated and undefined** — never store or model it
- `altHAE` = true geometric altitude above the WGS84 ellipsoid
- `altMSL` = `altHAE - geoidSep`
- `geoidSep` is computed from EGM2008 by gpsd when the receiver doesn't supply it (usually accurate to ±1m, worst case ±12m)
- For most carputer/navigation applications, `altMSL` is what users expect
- For precise RTK baselines and surveying, use `altHAE`

### `magvar` Sign Convention

**Positive = West, Negative = East.** This is the opposite of what most people expect. Double-check any heading correction code that uses this field.

### RTK Fields (`relN`, `relE`, `relD`)

These are only present when the ZED-F9P is in rover mode receiving RTK corrections from a base station. They represent the baseline vector (rover position relative to base), not absolute position. They appear alongside `status: 3` (Fixed) or `status: 4` (Float). If you are storing RTK solutions, these should be in your model.

### Error Estimates

All `ep*` fields and `sep` are **guessed** to be 95% confidence but the spec explicitly states certainty is unknown and the confidence level varies by receiver. Treat them as relative quality indicators, not absolute bounds. GST `lat`/`lon`/`alt` fields are 1-sigma standard deviations and are more formally defined.

### Multiple TPV Per Epoch

The spec allows multiple TPV objects per 1Hz epoch when a receiver dribbles data across several sentences. Your consumer must handle this. For a simple model, take the last TPV received that has `mode >= 2` within a given second. For a more robust model, merge partial updates using the timestamp as the epoch key.

### TOFF vs PPS for Timekeeping

| | TOFF | PPS |
|-|------|-----|
| Source | GPS serial data stream | Hardware pulse on TIMEPULSE pin |
| Typical error | 10ms–700ms | <10µs (real serial), <1ms (USB-serial) |
| Requires hardware wiring | No | Yes (`/dev/pps0`) |
| `precision` field | Absent (assumed -2) | Present |
| Use case | Sanity check, software-only | NTP discipline, precision timing |

---

## 18. Field Quick-Reference

### "Will this field be present?" Decision Tree

```
TPV received
├── mode == 0 or 1 → only class + mode reliable, discard
├── mode == 2 (2D fix)
│   ├── lat, lon → YES
│   ├── time     → YES (if receiver provides)
│   ├── speed, track → usually YES
│   ├── altHAE, altMSL → NO (need 3D)
│   └── ep* errors → maybe
└── mode == 3 (3D fix)
    ├── lat, lon, altHAE, altMSL → YES
    ├── speed, track, climb → usually YES
    ├── status → only if receiver supplies it (ZED-F9P does)
    ├── eph, sep → usually YES
    ├── relN/relE/relD → only when status == 3 or 4 (RTK)
    └── ecef* → only if receiver supplies it
```

### Units Summary

| Measurement | Unit |
|------------|------|
| Position | decimal degrees (WGS84) |
| Altitude | meters |
| Speed | m/s |
| Course/heading | degrees (0–360, true north unless noted) |
| Error estimates | meters (position), m/s (velocity), degrees (track), seconds (time) |
| Signal strength | dBHz |
| DOP values | dimensionless |
| PPS timing | seconds + nanoseconds (two separate fields) |
| OSC delta | nanoseconds |
| PPS `qErr` | picoseconds |
