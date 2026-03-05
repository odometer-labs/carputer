# Fake API - GPS Testing

This folder contains a fake API layer for testing the frontend with simulated GPS data.

## Overview

The fake API provides two modes for GPS data:

1. **Mock Data Mode** (default) - Replays positions from a local NMEA file, or falls back to random movement if the file can't be loaded.
2. **gpsfake Mode** - Connects to a real gpsfake + gpsd daemon via WebSocket bridge for realistic testing.

## Quick Start

### Option 1: Mock Data (No Setup Required)

The app replays the bundled NMEA file by default. Just run:

```bash
npm run dev
```

The map will show simulated GPS movement from the bundled route data.

### Option 2: Real GPS Data via gpsfake (Recommended)

**Prerequisites:** gpsd and gpsfake installed on your system (Linux/WSL).

**Terminal 1 - Start gpsfake:**

```bash
gpsfake -c 0.01 -n kras-en.nmea
```

OR for a route with heading changes:

```bash
gpsfake -c 0.01 -n kras-en-heading-changes.nmea
```

Flags:

- `-c 0.01` = 10ms delay between sentences (adjust for different speeds)
- `-n` = don't wait for client before starting

**Terminal 2 - Start GPS WebSocket bridge:**

```bash
cd frontend/carputer-web-app
npm run dev:gps
```

Expected output:

```
[gps-bridge] WebSocket listening on ws://0.0.0.0:8765
[gps-bridge] Connected to gpsd at 127.0.0.1:2947
```

**Terminal 3 - Start frontend dev server:**

```bash
npm run dev
```

The app will connect to `localhost:5173` (or similar).

**Terminal 4 - (Optional) Check browser console:**
Look for: `Connected to gpsfake server` in browser DevTools → Console.

### Option 3: Test on a Phone / Remote Device

The WebSocket host is resolved dynamically from `window.location.hostname`, so the app automatically connects to the right machine regardless of whether it's opened from `localhost` or a network IP.

**Terminal 1 - Start gpsfake (WSL or Linux):**

```bash
gpsfake -c 0.01 -n kras-en.nmea
```
OR

```bash
gpsfake -c 0.01 -n kras-en-heading-changes.nmea
```
**Terminal 2 - Start GPS WebSocket bridge:**

```bash
cd frontend/carputer-web-app
npm run dev:gps
```

**Terminal 3 - Start frontend with network access:**

```bash
npm run dev -- --host
```

Vite will print a **Network** URL like `http://192.168.x.x:5173`. Open that on your phone (must be on the same Wi-Fi network). The WebSocket bridge and GPS data will work without any extra configuration.

## Configuration

### Switch Between Mock and gpsfake

Edit `src/fake-api/config.ts` and change `USE_MOCK_DATA`:

```typescript
export const GPS_CONFIG = {
  USE_MOCK_DATA: true, // ← true = NMEA file playback, false = gpsfake WebSocket

  GPSFAKE: {
    port: 8765,
    // host is resolved at runtime from window.location.hostname so remote
    // devices automatically connect back to the correct machine.
    get host(): string {
      return typeof window !== "undefined"
        ? window.location.hostname
        : "localhost";
    },
  },

  MOCK: {
    updateInterval: 1000,
    defaultLocation: {
      latitude: 45.5147,
      longitude: -122.6819,
      altitude: 50,
      accuracy: 10,
    },
    movementVariation: 0.0001, // ~11 meters per update
    maxSpeed: 20, // m/s
  },
};
```

Or use the helper functions at runtime:

```typescript
import { useMockData, useGPSFake, toggleGPSMode } from "./config";

useMockData(); // Switch to NMEA file playback
useGPSFake(); // Switch to gpsfake WebSocket connection
toggleGPSMode(); // Toggle between the two modes
```

### Component Usage

```typescript
import { gpsService } from "../fake-api/gpsService";

onMount(() => {
  gpsService.start(
    (position) => {
      console.log("GPS Position:", position);
      // position.latitude, position.longitude, position.heading, position.speed
    },
    (error) => {
      console.error("GPS Error:", error);
    },
  );

  return () => {
    gpsService.stop();
  };
});
```

## gpsfake Speed Options

Adjust the `-c` flag to control playback speed:

```bash
gpsfake -c 0.01 -n file.nmea   # Very fast (~100 Hz) — hard to follow on map
gpsfake -c 0.05 -n file.nmea   # Fast
gpsfake -c 0.1  -n file.nmea   # Moderate (10 Hz) — good for debugging
gpsfake -c 1.0  -n file.nmea   # Slow (1 update/sec)
gpsfake -S      -n file.nmea   # Ultra-realistic timing from NMEA timestamps
```

## Troubleshooting

**Map shows blue dot but no movement**

- Check browser console for `Connected to gpsfake server`
- Verify gpsd is running: `telnet localhost 2947`
- Verify bridge is running on port `8765`
- Try restarting all three processes in order: gpsfake → bridge → dev server

**No GPS updates visible**

- Ensure `USE_MOCK_DATA` is `false` in `config.ts` if using gpsfake
- Check that `kras-en.nmea` exists and contains valid NMEA sentences
- Look for `[gps-bridge]` logs in the bridge terminal

**Phone can't connect to WebSocket**

- Confirm phone is on the same Wi-Fi network as your dev machine
- Confirm the dev server was started with `--host`: `npm run dev -- --host`
- Confirm the bridge is running (`npm run dev:gps`) — it must bind to `0.0.0.0:8765`, not just `localhost`
- Check that your firewall allows inbound connections on ports `5173` and `8765`

**Frontend loads but map is blank/slow**

- Reduce gpsfake playback speed (use a higher `-c` value, e.g. `0.5`)
- Check browser Network tab → WS tab for WebSocket connection status
- Open DevTools Console and confirm GPS position updates are logging

## Files

- `gpsService.ts` - Main GPS service (NMEA file playback + gpsfake WebSocket)
- `types.ts` - TypeScript types for GPS data and service configuration
- `config.ts` - Centralized configuration (mode toggle, ports, mock defaults)
- `kras-en.nmea` - Bundled NMEA route file used for mock playback
- `kras-en-heading-changes.nmea` - Alternate route with more frequent heading changes

## Notes

- This folder is temporary and should be removed when the real backend GPS integration is complete
- Mock mode defaults to replaying `kras-en.nmea`; falls back to random movement if the file can't be fetched
- Default mock location is Portland State University (45.5147°N, 122.6819°W)
