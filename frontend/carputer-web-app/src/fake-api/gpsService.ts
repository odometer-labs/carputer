/**
 * GPS Service - Connects to gpsfake or provides mock GPS data
 * This service abstracts away the GPS data source (gpsfake or simulated)
 */

import type {
  GPSPosition,
  GPSServiceConfig,
  GPSUpdateCallback,
  GPSErrorCallback,
} from "./types";
import { GPS_CONFIG } from "./config";

export class GPSService {
  private config: Required<GPSServiceConfig>;
  private onUpdate: GPSUpdateCallback | null = null;
  private onError: GPSErrorCallback | null = null;
  private ws: WebSocket | null = null;
  private mockInterval: number | null = null;
  private mockPosition: GPSPosition;

  constructor(config: GPSServiceConfig = {}) {
    this.config = {
      useMockData: config.useMockData ?? GPS_CONFIG.USE_MOCK_DATA,
      gpsfakePort: config.gpsfakePort ?? GPS_CONFIG.GPSFAKE.port,
      gpsfakeHost: config.gpsfakeHost ?? GPS_CONFIG.GPSFAKE.host,
      mockUpdateInterval:
        config.mockUpdateInterval ?? GPS_CONFIG.MOCK.updateInterval,
    };

    // Initial mock position
    this.mockPosition = {
      latitude: GPS_CONFIG.MOCK.defaultLocation.latitude,
      longitude: GPS_CONFIG.MOCK.defaultLocation.longitude,
      altitude: GPS_CONFIG.MOCK.defaultLocation.altitude,
      accuracy: GPS_CONFIG.MOCK.defaultLocation.accuracy,
      heading: 0,
      speed: 0,
      timestamp: Date.now(),
    };
  }

  /**
   * Start listening for GPS updates
   */
  public start(onUpdate: GPSUpdateCallback, onError?: GPSErrorCallback): void {
    this.onUpdate = onUpdate;
    this.onError = onError || (() => {});

    if (this.config.useMockData) {
      this.startMockGPS();
    } else {
      this.connectToGPSFake();
    }
  }

  /**
   * Stop listening for GPS updates
   */
  public stop(): void {
    if (this.mockInterval) {
      clearInterval(this.mockInterval);
      this.mockInterval = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Start mock GPS data generation
   */
  private startMockGPS(): void {
    // Simulate movement in a small area
    this.mockInterval = window.setInterval(() => {
      // Add small random variations to position
      this.mockPosition.latitude +=
        (Math.random() - 0.5) * GPS_CONFIG.MOCK.movementVariation;
      this.mockPosition.longitude +=
        (Math.random() - 0.5) * GPS_CONFIG.MOCK.movementVariation;
      // Add small random variation to heading (±5 degrees)
      this.mockPosition.heading =
        ((this.mockPosition.heading ?? 0) + (Math.random() - 0.5) * 10 + 360) %
        360;
      this.mockPosition.speed = Math.random() * GPS_CONFIG.MOCK.maxSpeed;
      this.mockPosition.timestamp = Date.now();

      if (this.onUpdate) {
        this.onUpdate(this.mockPosition);
      }
    }, this.config.mockUpdateInterval);

    // Send initial position immediately
    if (this.onUpdate) {
      this.onUpdate(this.mockPosition);
    }
  }

  /**
   * Connect to gpsfake WebSocket server
   */
  private connectToGPSFake(): void {
    try {
      const url = `ws://${this.config.gpsfakeHost}:${this.config.gpsfakePort}`;
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log("Connected to gpsfake server");
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          const latitudeRaw = data.latitude ?? data.lat;
          const longitudeRaw = data.longitude ?? data.lon;

          if (!Number.isFinite(latitudeRaw) || !Number.isFinite(longitudeRaw)) {
            return;
          }

          const latitude = Number(latitudeRaw);
          const longitude = Number(longitudeRaw);

          if (Math.abs(latitude) > 90 || Math.abs(longitude) > 180) {
            return;
          }

          const headingRaw = data.heading ?? data.bearing ?? data.track;
          const heading = Number.isFinite(headingRaw)
            ? ((Number(headingRaw) % 360) + 360) % 360
            : undefined;

          const altitudeRaw = data.altitude ?? data.alt ?? data.altHAE;
          const speedRaw = data.speed;
          const accuracyRaw = data.accuracy ?? data.eph;
          const timestampRaw = data.timestamp;

          const gpsData: GPSPosition = {
            latitude,
            longitude,
            altitude: Number.isFinite(altitudeRaw)
              ? Number(altitudeRaw)
              : undefined,
            accuracy: Number.isFinite(accuracyRaw)
              ? Number(accuracyRaw)
              : undefined,
            heading,
            speed: Number.isFinite(speedRaw) ? Number(speedRaw) : undefined,
            timestamp: Number.isFinite(timestampRaw)
              ? Number(timestampRaw)
              : Date.now(),
          };

          if (this.onUpdate) {
            this.onUpdate(gpsData);
          }
        } catch (error) {
          if (this.onError) {
            this.onError(`Failed to parse GPS data: ${error}`);
          }
        }
      };

      this.ws.onerror = (error: Event) => {
        if (this.onError) {
          this.onError(`WebSocket error: ${error}`);
        }
        // Fallback to mock data if gpsfake fails
        console.warn("gpsfake connection failed, falling back to mock data");
        this.config.useMockData = true;
        this.startMockGPS();
      };

      this.ws.onclose = () => {
        console.log("Disconnected from gpsfake server");
      };
    } catch (error) {
      if (this.onError) {
        this.onError(`Failed to connect to gpsfake: ${error}`);
      }
      // Fallback to mock data
      this.config.useMockData = true;
      this.startMockGPS();
    }
  }

  /**
   * Set mock position for testing
   */
  public setMockPosition(position: Partial<GPSPosition>): void {
    this.mockPosition = {
      ...this.mockPosition,
      ...position,
      timestamp: Date.now(),
    };

    if (this.onUpdate) {
      this.onUpdate(this.mockPosition);
    }
  }

  /**
   * Get current mock position
   */
  public getMockPosition(): GPSPosition {
    return { ...this.mockPosition };
  }
}

// Export singleton instance
export const gpsService = new GPSService({
  useMockData: GPS_CONFIG.USE_MOCK_DATA,
  mockUpdateInterval: GPS_CONFIG.MOCK.updateInterval,
});
