# Fake API - GPS Testing

This folder contains a fake API layer for testing the frontend with simulated GPS data.

## Overview

The fake API provides two modes for GPS data:

1. **Mock Data Mode** (default) - Generates simulated GPS positions with random variations
2. **gpsfake Mode** - Connects to a real gpsfake + gpsd daemon via WebSocket bridge for realistic testing

## Quick Start

### Option 1: Mock Data (No Setup Required)

The frontend uses mock data by default. Just run:

```bash
npm run dev
```

The map will show simulated GPS movement around Portland State University.

### Option 2: Real GPS Data via gpsfake (Recommended)

**Prerequisites:** gpsd and gpsfake installed on your system (Linux/WSL).

**Terminal 1 - Start gpsfake:**

```bash
gpsfake -c 0.05 -n kras-en.nmea
```

Replace `kras-en.nmea` with your NMEA log file path. Flags:

- `-c 0.05` = 50ms delay between sentences (adjust for different speeds)
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

## Configuration

### Switch Between Mock and gpsfake

Edit `src/fake-api/config.ts`:

```typescript
export const GPS_CONFIG = {
  USE_MOCK_DATA: false, // ← Change this: true = mock, false = gpsfake connection

  GPSFAKE: {
    port: 8765,
    host: "localhost",
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

Or use helper functions:

```typescript
import { useMockData, useGPSFake, toggleGPSMode } from "./config";

useMockData(); // Switch to mock data
useGPSFake(); // Switch to gpsfake connection
toggleGPSMode(); // Toggle between modes
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

Adjust `-c` flag to control playback speed:

```bash
# Very fast (hard to see on map)
gpsfake -c 0.01 -n file.nmea

# Fast (0.01s = 100 Hz)
gpsfake -c 0.05 -n file.nmea

# Moderate (0.1s = 10 Hz) - good for debugging
gpsfake -c 0.1 -n file.nmea

# Slow (1s between updates)
gpsfake -c 1.0 -n file.nmea

# Ultra-realistic delays
gpsfake -S -n file.nmea
```

## Troubleshooting

**Map shows blue dot and black background**

- Check browser console for `Connected to gpsfake server`
- Verify gpsd is running on `localhost:2947`
- Verify bridge is running on `localhost:8765`
- Try restarting all three processes

**No GPS updates visible**

- Ensure `USE_MOCK_DATA` is `false` in `config.ts`
- Check that `kras-en.nmea` file exists and has valid NMEA sentences
- Look for `[gps-bridge]` logs in bridge terminal

**Bridge won't connect to gpsd**

- Verify gpsfake started successfully (check for `connected to` message)
- Try: `telnet localhost 2947` to test gpsd connection
- Check that gpsd port hasn't changed

**Frontend loads but map is blank/slow**

- Reduce playback speed: use higher `-c` value (e.g., `0.5`)
- Check browser Network tab for WebSocket connections
- Open DevTools Console and verify GPS position updates logging

## Files

- `gpsService.ts` - Main GPS service with mock and gpsfake connection logic
- `types.ts` - TypeScript types for GPS data and configuration
- `config.ts` - Centralized configuration for all GPS settings

## Notes

- This folder is temporary and should be removed when the backend is fully functional
- Currently defaults to mock data mode for easy frontend testing
- Mock data simulates movement around Portland State University area (45.5147°N, 122.6819°W)
