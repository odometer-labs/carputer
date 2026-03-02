/**
 * GPS data types for the fake API
 * Used to standardize GPS data from gpsfake or simulated sources
 */

export interface GPSPosition {
  latitude: number;
  longitude: number;
  altitude?: number;
  accuracy?: number;
  heading?: number;
  speed?: number;
  timestamp: number;
}

export interface GPSServiceConfig {
  // Use mock data if true, otherwise connect to gpsfake
  useMockData?: boolean;
  // Port for gpsfake WebSocket server
  gpsfakePort?: number;
  // Host for gpsfake server
  gpsfakeHost?: string;
  // Update interval for mock data (ms)
  mockUpdateInterval?: number;
}

export type GPSUpdateCallback = (position: GPSPosition) => void;
export type GPSErrorCallback = (error: string) => void;
