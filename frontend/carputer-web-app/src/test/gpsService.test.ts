import { vi, describe, it, expect } from "vitest";
import { GPSService } from "../fake-api/gpsService";
import { GPS_CONFIG } from "../fake-api/config";

vi.useFakeTimers();

describe("GPSService mock behavior", () => {
  it("generates updates when using random mock data", () => {
    // force the global config so start() picks the mock path
    GPS_CONFIG.USE_MOCK_DATA = true;

    const service = new GPSService({
      useMockData: true,
      useNMEAPlayback: false,
      mockUpdateInterval: 1000,
    });
    const updates: unknown[] = [];
    service.start((pos) => {
      updates.push(pos);
    });

    // advance a few intervals
    vi.advanceTimersByTime(3500);

    expect(updates.length).toBeGreaterThan(0);
    service.stop();
  });

  it("bare start/stop sequence does not throw", () => {
    const service = new GPSService();
    service.start(() => {});
    service.stop();
  });
});
