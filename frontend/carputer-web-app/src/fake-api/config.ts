/**
 * GPS Configuration
 *
 * Toggle between mock data and gpsfake here for quick testing
 * This is the single source of truth for GPS behavior
 */

export const GPS_CONFIG = {
  // Set to true for mock data, false to connect to gpsfake
  USE_MOCK_DATA: false,

  // gpsfake WebSocket server configuration
  // Host defaults to whatever hostname the page was loaded from, so that
  // remote devices (phones on the same network via --host) automatically
  // connect back to the dev machine instead of their own localhost.
  GPSFAKE: {
    port: 8765,
    get host(): string {
      return typeof window !== "undefined"
        ? window.location.hostname
        : "localhost";
    },
  },

  // Mock data configuration
  MOCK: {
    // Update interval in milliseconds
    updateInterval: 1000,

    // Default starting position (Portland State University)
    defaultLocation: {
      latitude: 45.5147,
      longitude: -122.6819,
      altitude: 50,
      accuracy: 10,
    },

    // Maximum variation per update (in degrees)
    // 0.0001 degrees ≈ 11 meters at equator
    movementVariation: 0.0001,

    // Speed range for mock data (m/s)
    maxSpeed: 20,
  },
};

/**
 * Quick toggle functions for testing
 */

export function useMockData(): void {
  GPS_CONFIG.USE_MOCK_DATA = true;
  console.log("GPS Mode: MOCK DATA");
}

export function useGPSFake(): void {
  GPS_CONFIG.USE_MOCK_DATA = false;
  console.log("GPS Mode: GPSFAKE CONNECTION");
}

export function toggleGPSMode(): void {
  GPS_CONFIG.USE_MOCK_DATA = !GPS_CONFIG.USE_MOCK_DATA;
  console.log(
    `GPS Mode: ${GPS_CONFIG.USE_MOCK_DATA ? "MOCK DATA" : "GPSFAKE"}`,
  );
}
