# Frontend GPS Testing Setup - Quick Guide

This guide explains how to test the Carputer frontend with simulated GPS data using the fake API.

## ✅ What's Configured

The frontend now includes a **fake API layer** in `src/fake-api/` that provides GPS data for testing. By default, it uses **mock GPS data** that simulates movement around Portland State University.

## 🚀 Getting Started

### Option 1: Use Mock Data (Default - No Setup Required)

The frontend is already configured to use mock GPS data. Simply run the frontend:

```bash
cd frontend/carputer-web-app
npm run dev
```

The map will:

- Start at Portland State University (45.5147°N, 122.6819°W)
- Show a blue marker at your "location"
- Simulate small random movements every second
- Update the location display at the bottom

### Option 2: Connect to gpsfake (Real GPS Simulation)

If you want to use actual GPS data from gpsfake:

1. **Start gpsfake** on your system with WebSocket support on port 8765
2. **Edit** `src/fake-api/gpsService.ts`:
   ```typescript
   export const gpsService = new GPSService({
     useMockData: false, // ← Change this to false
     gpsfakePort: 8765,
     gpsfakeHost: "localhost",
     mockUpdateInterval: 1000,
   });
   ```
3. **Reload** the frontend in your browser

If gpsfake is not running or connection fails, the service automatically falls back to mock data.

## 📁 File Structure

```
frontend/carputer-web-app/src/fake-api/
├── README.md           # Full API documentation
├── types.ts            # TypeScript types for GPS data
└── gpsService.ts       # Main GPS service (mock + gpsfake connection)
```

## 🔧 Configuration Options

Edit `src/fake-api/gpsService.ts` constructor parameters:

| Parameter            | Type    | Default     | Description                             |
| -------------------- | ------- | ----------- | --------------------------------------- |
| `useMockData`        | boolean | true        | true = mock, false = gpsfake connection |
| `gpsfakePort`        | number  | 8765        | WebSocket port for gpsfake              |
| `gpsfakeHost`        | string  | 'localhost' | Host/IP for gpsfake server              |
| `mockUpdateInterval` | number  | 1000        | Update frequency in milliseconds        |

## 📍 Default Mock Location

Portland State University area:

- **Latitude**: 45.5147°N
- **Longitude**: 122.6819°W
- **Altitude**: 50m
- **Initial Speed**: 0 m/s

Mock data generates random movements ±0.0001° (~11 meters) per update.

## 🗑️ Cleanup

This fake API folder is **temporary** and should be removed when:

- Backend GPS service is fully functional
- Hardware GPS integration is complete
- WebSocket connection to backend is established

At that point, replace `gpsService` calls with actual backend API calls.

## 🐛 Troubleshooting

### No GPS data appears on map

- Check browser console for errors
- Verify `src/fake-api/gpsService.ts` is properly imported
- Try refreshing the page

### Map doesn't center on location

- Ensure OpenLeaflet (ol) library is installed
- Check that `map` variable is properly initialized

### Want different starting location

- Edit `mockPosition` in `src/fake-api/gpsService.ts`
- Change latitude/longitude values

### gpsfake connection fails

- Verify gpsfake is running on the configured port
- Check firewall settings
- Service will automatically fall back to mock data
