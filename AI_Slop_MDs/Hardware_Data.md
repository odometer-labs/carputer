# GPS Module Identification - ZED-F9T-00B

## Module Identification

### Primary Module: u-blox ZED-F9T-00B

**Visible on the white chip in the center of the board:**
- Manufacturer: u-blox
- Model: ZED-F9T-00B
- Part Number: ZED-F9T-00B-01

**Module Type:** High-Precision Multi-Band GNSS Timing Module

---

## Breakout Board

**Board Characteristics:**
- **Color:** Red PCB with white silkscreen
- **Manufacturer:** SparkFun Electronics (typical design pattern)
- **Likely Product:** SparkFun GPS-RTK Dead Reckoning Breakout - ZED-F9T (Qwiic)
- **Estimated Product Code:** GPS-19029 or similar variant

**Visible Features:**
- SMA connector (gold, bottom left) - for external active GPS antenna
- Coin cell battery holder (right side) - for GPS backup/hot start
- Multiple interface pins broken out:
  - GND, TXD, RXD (UART)
  - SDA, SCL (I2C)
  - 3V3, 5V (Power)
  - Additional GPIO and control pins
- Professional PCB layout with proper labeling
- Likely includes Qwiic connector (SparkFun's I2C connector system)

---

## Technical Specifications

### GNSS Capabilities

**Supported Constellations:**
- GPS (L1C/A, L2C)
- GLONASS (L1OF, L2OF)
- Galileo (E1-B/C, E5b)
- BeiDou (B1I, B2I)
- QZSS (L1C/A, L2C) - Japan regional system

**Multi-Band Reception:**
- Simultaneous L1 and L2/E5b band reception
- Superior ionospheric error correction
- Better multipath rejection
- Enhanced accuracy in challenging environments

### Performance Specifications

| Specification | Value |
|--------------|-------|
| **Timing Accuracy** | 5 ns (1-sigma) RMS |
| **Time Pulse Accuracy** | 5 ns RMS |
| **Position Accuracy** | 2.5 m CEP (L1 only) |
| **Position Accuracy** | 1.5 m CEP (Multi-band) |
| **Sensitivity** | -167 dBm (tracking) |
| **Max Update Rate** | 10 Hz (10 times/second) |
| **Cold Start** | ~26 seconds |
| **Hot Start** | ~1 second (with battery backup) |
| **Channels** | 184 tracking channels |

### Electrical Specifications

| Parameter | Specification |
|-----------|--------------|
| **Supply Voltage** | 2.7V - 3.6V (module) |
| **Breakout Board** | 3.3V or 5V compatible |
| **Current Consumption** | ~60 mA (tracking) |
| **Current Consumption** | ~100 mA (acquisition) |
| **Operating Temp** | -40°C to +85°C |
| **Storage Temp** | -40°C to +85°C |

### Physical Specifications

**Module:**
- **Package:** 54-pin LGA (Land Grid Array)
- **Dimensions:** 22mm x 17mm x 2.5mm
- **Weight:** <3 grams

**Breakout Board:**
- **Approximate Dimensions:** ~50mm x 50mm
- **Mounting Holes:** 4 corners (standard SparkFun pattern)

---

## Communication Interfaces

### Available Interfaces

**UART (Primary for Raspberry Pi):**
- Default baud rate: 9600 (configurable up to 921,600)
- TX/RX pins broken out on board
- 3.3V logic level

**I2C:**
- Fast mode: 400 kHz
- Address: 0x42 (default)
- SDA/SCL pins available
- Qwiic connector (if SparkFun board)

**SPI:**
- Up to 5.5 MHz clock
- MISO/MOSI/CS/CLK available
- Selectable via configuration

**USB (if board has it):**
- Some SparkFun variants include USB-C connector
- Direct connection to computer for configuration
- U-center software compatible

---

## Key Advantages for Carputer Project

### 1. **Superior Accuracy**
- Multi-band reception reduces ionospheric errors
- Better accuracy in urban canyons (buildings)
- L1+L2 provides 1.5m accuracy vs. 2.5m for L1-only

### 2. **Excellent Timing**
- 5 nanosecond timing accuracy
- Perfect for precise timestamping of track points
- Ideal for time synchronization if needed

### 3. **Fast Acquisition**
- Hot start in ~1 second (with battery backup)
- Cold start in ~26 seconds
- Battery backup ensures quick re-acquisition after power loss

### 4. **High Update Rate**
- Up to 10 Hz (10 position updates/second)
- Smoother track recording
- Better for detecting rapid direction changes

### 5. **Robust Performance**
- Multi-constellation support (GPS + GLONASS + Galileo + BeiDou)
- More satellites visible = better reliability
- Works well in partially obstructed environments

---

## Comparison: Standard vs. High-Precision GPS

| Feature | Standard GPS (NEO-M8N) | This Module (ZED-F9T) |
|---------|----------------------|---------------------|
| **Bands** | L1 only | L1 + L2/E5b |
| **Accuracy** | ~2.5m | ~1.5m (multi-band) |
| **Timing** | ~30 ns | ~5 ns |
| **Update Rate** | 1-10 Hz | 1-10 Hz |
| **Constellations** | GPS + GLONASS + Galileo + BeiDou | GPS + GLONASS + Galileo + BeiDou |
| **Channels** | 72 | 184 |
| **Price** | ~$40 | ~$200 |
| **Use Case** | Standard tracking | High-precision tracking/timing |

**Bottom Line:** The ZED-F9T is significant overkill for basic car tracking, but will provide excellent accuracy and reliability!

---

## Integration with Carputer Project

### Hardware Connection to Raspberry Pi

**Recommended: UART Connection**

```
ZED-F9T Breakout → Raspberry Pi
TXD  →  RXD (GPIO 15, Pin 10)
RXD  →  TXD (GPIO 14, Pin 8)
3V3  →  3.3V (Pin 1)
GND  →  GND (Pin 6)
```

**Alternative: I2C Connection (if preferred)**

```
ZED-F9T Breakout → Raspberry Pi
SDA  →  SDA (GPIO 2, Pin 3)
SCL  →  SCL (GPIO 3, Pin 5)
3V3  →  3.3V (Pin 1)
GND  →  GND (Pin 6)
```

**Antenna Connection:**
- **Required:** Active GPS antenna (3.3V or 5V powered)
- **Connector:** SMA male to board's SMA female
- **Recommended:** Magnetic mount GPS antenna for car roof
- **Frequency:** 1575.42 MHz (L1) + 1227.60 MHz (L2)
- **Cable Length:** 3-5 meters recommended

### Software Configuration

**Step 1: Disable Serial Console (for UART)**
```bash
sudo raspi-config
# Interface Options → Serial Port
#   Login shell over serial? → No
#   Serial port hardware enabled? → Yes
```

**Step 2: Enable UART in Boot Config**
```bash
echo "enable_uart=1" | sudo tee -a /boot/config.txt
sudo reboot
```

**Step 3: Install gpsd**
```bash
sudo apt update
sudo apt install gpsd gpsd-clients python3-gps
```

**Step 4: Configure gpsd**
```bash
sudo nano /etc/default/gpsd
```

**Add/modify these lines:**
```
DEVICES="/dev/serial0"
GPSD_OPTIONS="-n"
START_DAEMON="true"
```

**Step 5: Restart gpsd**
```bash
sudo systemctl enable gpsd
sudo systemctl restart gpsd
```

**Step 6: Test GPS**
```bash
cgps -s
```

You should see:
- Satellite count increasing
- Position lock within 30 seconds
- Lat/Lon coordinates
- Speed, heading, altitude

---

## Expected Data Output

### gpsd JSON Format (Same as Documented)

```json
{
  "class": "TPV",
  "device": "/dev/serial0",
  "mode": 3,
  "time": "2026-02-12T18:30:45.000Z",
  "lat": 45.523062,
  "lon": -122.676482,
  "alt": 15.6,
  "track": 84.4,
  "speed": 13.89,
  "climb": 0.2,
  "epx": 1.5,
  "epy": 1.8,
  "epv": 3.2,
  "eph": 2.1
}
```

**Note:** The ZED-F9T will provide **better accuracy** in the error estimates (epx, epy, eph) due to multi-band reception.

---

## Advanced Features (Optional)

### UBX Protocol Configuration

The ZED-F9T supports u-blox's proprietary UBX protocol for advanced configuration:

**Using u-center (Windows software):**
- Configure update rates
- Enable/disable specific GNSS systems
- Adjust power modes
- Configure timing outputs
- Save configurations to module

**Using Python (ubxtranslator library):**
```bash
pip install ubxtranslator
```

### High-Precision Timing Output

The module has a **TIME_PULSE** output that can provide:
- Precise 1 PPS (pulse per second) signal
- Configurable frequency outputs
- Nanosecond-level accuracy
- Useful for time synchronization applications

---

## Troubleshooting

### No GPS Fix

**Symptom:** `mode: 0` or `mode: 1` in gpsd
**Causes:**
1. **No antenna connected** → Connect active GPS antenna to SMA
2. **Antenna not powered** → Check antenna gets 3.3V or 5V
3. **Antenna not visible to sky** → Move antenna near window or outside
4. **Cold start delay** → Wait up to 60 seconds for first fix

### Solution:
```bash
# Check gpsd status
sudo systemctl status gpsd

# View raw NMEA data
cat /dev/serial0

# Check device permissions
ls -l /dev/serial0
```

### Antenna Requirements

**Critical:** This module **requires an active GPS antenna**

**Recommended Antenna Specs:**
- Frequency: L1/L2 dual-band (1575.42 MHz + 1227.60 MHz)
- Gain: 28-35 dB
- LNA: Built-in low-noise amplifier
- Power: 3.3V or 5V (check antenna specs)
- Connector: SMA male
- Cable: Low-loss coaxial, 3-5m

**Example Antennas:**
- Tallysman TW3972 (dual-band, high-performance)
- Survey-grade L1/L2 patch antennas
- Any L1/L2 active GPS antenna with SMA connector

---

## Data Sheet & Resources

**Official Documentation:**
- Data Sheet: ZED-F9T-00B_DataSheet_UBX-18053713.pdf
- Integration Manual: ZED-F9T_IntegrationManual
- Interface Description: u-blox F9 Interface Description

**Software Tools:**
- u-center: Windows configuration software
- u-center 2: Cross-platform configuration tool

**Online Resources:**
- u-blox Product Page: https://www.u-blox.com/en/product/zed-f9t-module
- SparkFun Hookup Guide: (if SparkFun board)
- u-blox Documentation: https://www.u-blox.com/en/product-resources

---

## Cost & Availability

**Module Cost:** ~$199 USD (DigiKey, Mouser)
**SparkFun Breakout:** ~$230-250 USD
**Required Antenna:** ~$50-150 USD (depending on quality)

**Total Investment:** ~$300-400 for complete GPS setup

---

## Summary for Your Carputer Project

### What You Have
✅ **High-precision multi-band GNSS module**
✅ **Professional breakout board** with all interfaces
✅ **Battery backup** for fast re-acquisition
✅ **Active antenna support** via SMA connector

### What You Need
- [ ] **Active L1/L2 GPS antenna** (SMA connector, 3-5m cable)
- [ ] **Magnetic mount** (for car roof placement)
- [ ] **Dupont wires** (to connect to Raspberry Pi GPIO)

### Integration Status
- ✅ **Compatible with gpsd** - Same interface as any u-blox module
- ✅ **Data format documented** - See GPS Data Format Reference doc
- ✅ **Better than expected accuracy** - Multi-band = 1.5m vs. 2.5m
- ✅ **Perfect for carputer** - Fast acquisition, high accuracy, reliable

### Next Steps
1. **Order active L1/L2 GPS antenna** with SMA connector
2. **Connect to Raspberry Pi** via UART (TXD/RXD)
3. **Install and configure gpsd** (instructions above)
4. **Test GPS fix** using `cgps -s`
5. **Integrate with backend** using Python gpsd client

---
