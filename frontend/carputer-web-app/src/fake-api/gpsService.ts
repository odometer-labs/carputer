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
  private nmeaPositions: GPSPosition[] = [];
  private currentPositionIndex: number = 0;
  private nmeaFileLoaded: boolean = false;

  constructor(config: GPSServiceConfig = {}) {
    this.config = {
      useMockData: config.useMockData ?? GPS_CONFIG.USE_MOCK_DATA,
      gpsfakePort: config.gpsfakePort ?? GPS_CONFIG.GPSFAKE.port,
      gpsfakeHost: config.gpsfakeHost ?? GPS_CONFIG.GPSFAKE.host,
      mockUpdateInterval:
        config.mockUpdateInterval ?? GPS_CONFIG.MOCK.updateInterval,
      useNMEAPlayback:
        config.useNMEAPlayback ?? GPS_CONFIG.MOCK.useNMEAPlayback,
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
    // Stop any existing session before starting a new one.
    this.stop();

    this.onUpdate = onUpdate;
    this.onError = onError || (() => {});

    // Read the latest values so runtime config changes are respected.
    this.config.useMockData = GPS_CONFIG.USE_MOCK_DATA;
    this.config.gpsfakePort = GPS_CONFIG.GPSFAKE.port;
    this.config.gpsfakeHost = GPS_CONFIG.GPSFAKE.host;
    this.config.mockUpdateInterval = GPS_CONFIG.MOCK.updateInterval;
    this.config.useNMEAPlayback = GPS_CONFIG.MOCK.useNMEAPlayback;

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
   * Start mock GPS data generation - loads from NMEA file or falls back to random
   */
  private startMockGPS(): void {
    this.resetMockPositionToDefault();

    if (!this.config.useNMEAPlayback) {
      this.startRandomGPS();
      return;
    }

    this.loadNMEAFile().then((positions) => {
      if (positions.length > 0) {
        this.nmeaPositions = positions;
        this.currentPositionIndex = 0;
        this.startNMEAPlayback();
      } else {
        // Fallback to random GPS if NMEA file couldn't be loaded
        this.startRandomGPS();
      }
    });
  }

  /**
   * Reset mock coordinates to configured defaults.
   */
  private resetMockPositionToDefault(): void {
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
   * Replay GPS data from NMEA file
   */
  private startNMEAPlayback(): void {
    // Send initial position immediately
    if (this.onUpdate && this.nmeaPositions.length > 0) {
      const position = this.nmeaPositions[0];

      if (
        position &&
        Number.isFinite(position.latitude) &&
        Number.isFinite(position.longitude)
      ) {
        this.mockPosition = {
          latitude: position.latitude as number,
          longitude: position.longitude as number,
          altitude: position.altitude,
          accuracy: position.accuracy,
          heading: position.heading,
          speed: position.speed,
          timestamp: Date.now(),
        };
        this.onUpdate(this.mockPosition);
      }
    }

    // Iterate through NMEA positions
    this.mockInterval = window.setInterval(() => {
      if (this.nmeaPositions.length === 0) return;

      const position = this.nmeaPositions[this.currentPositionIndex];
      if (
        position &&
        Number.isFinite(position.latitude) &&
        Number.isFinite(position.longitude)
      ) {
        this.mockPosition = {
          latitude: position.latitude as number,
          longitude: position.longitude as number,
          altitude: position.altitude,
          accuracy: position.accuracy,
          heading: position.heading,
          speed: position.speed,
          timestamp: Date.now(),
        };
        this.currentPositionIndex =
          (this.currentPositionIndex + 1) % this.nmeaPositions.length;

        if (this.onUpdate) {
          this.onUpdate(this.mockPosition);
        }
      }
    }, this.config.mockUpdateInterval);
  }

  /**
   * Simulate movement with random variations (fallback)
   */
  private startRandomGPS(): void {
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
   * Load and parse NMEA file
   */
  private async loadNMEAFile(): Promise<GPSPosition[]> {
    if (this.nmeaFileLoaded) {
      return this.nmeaPositions;
    }

    try {
      const response = await fetch("/src/fake-api/kras-en.nmea");
      if (!response.ok) {
        throw new Error(`Failed to load NMEA file: ${response.statusText}`);
      }

      const text = await response.text();
      const lines = text.split("\n");

      const positions: GPSPosition[] = [];
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("$GPRMC")) {
          const position = this.parseNMEASentence(trimmed);
          if (
            position &&
            Number.isFinite(position.latitude) &&
            Number.isFinite(position.longitude)
          ) {
            positions.push(position);
          }
        }
      }

      this.nmeaFileLoaded = true;
      this.nmeaPositions = positions;
      return positions;
    } catch (error) {
      console.error("Failed to load NMEA file:", error);
      return [];
    }
  }

  /**
   * Parse NMEA GPRMC sentence to extract GPS data
   * Format: $GPRMC,time,status,lat,lat_dir,lon,lon_dir,speed,heading,date,mag_var,mag_var_dir*checksum
   */
  private parseNMEASentence(sentence: string): GPSPosition | null {
    try {
      // Remove $ and checksum
      const cleanSentence = sentence.replace(/^\$|[\*\w]{2}$/g, "");
      const fields = cleanSentence.split(",");

      if (fields[0] !== "GPRMC" || fields.length < 9) {
        return null;
      }

      // Extract fields
      const status = fields[2]; // A = active, V = void
      if (status !== "A") {
        return null; // Skip invalid data
      }

      // Parse latitude (format: DDMM.MMMM)
      const latRaw = fields[3];
      const latDir = fields[4];
      if (!latRaw || !latDir) return null;
      const lat = this.parseNMEACoordinate(latRaw, latDir);
      if (!lat) return null;

      // Parse longitude (format: DDDMM.MMMM)
      const lonRaw = fields[5];
      const lonDir = fields[6];
      if (!lonRaw || !lonDir) return null;
      const lon = this.parseNMEACoordinate(lonRaw, lonDir);
      if (!lon) return null;

      // Parse speed (in knots)
      const speedKnots = parseFloat(fields[7] ?? "");
      const speed = Number.isFinite(speedKnots) ? speedKnots : undefined;

      // Parse heading (course over ground in degrees)
      const headingStr = fields[8] ?? "";
      const heading = Number.isFinite(parseFloat(headingStr))
        ? parseFloat(headingStr)
        : undefined;

      return {
        latitude: lat,
        longitude: lon,
        heading,
        speed,
        altitude: undefined,
        accuracy: undefined,
        timestamp: Date.now(),
      };
    } catch (error) {
      return null;
    }
  }

  /**
   * Parse NMEA coordinate (lat/lon) to decimal degrees
   * Latitude format: DDMM.MMMM (2 digits degrees, 2 digits minutes)
   * Longitude format: DDDMM.MMMM (3 digits degrees, 2 digits minutes)
   */
  private parseNMEACoordinate(coord: string, direction: string): number | null {
    try {
      const value = parseFloat(coord);
      if (!Number.isFinite(value)) return null;

      // Extract degrees and minutes
      const isLongitude = coord.length > 9;
      const degreeLength = isLongitude ? 3 : 2;
      const degrees = Math.floor(value / 100);
      const minutes = value % 100;

      let decimal = degrees + minutes / 60;

      // Apply direction
      if (direction === "S" || direction === "W") {
        decimal = -decimal;
      }

      return decimal;
    } catch (error) {
      return null;
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
