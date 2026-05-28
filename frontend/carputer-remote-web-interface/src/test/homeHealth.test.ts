import { describe, expect, it } from "vitest";
import {
  deriveSystemHealthStatus,
  formatBytes,
  formatRate,
  formatUptime,
  getLatestVersionNumber,
  UNAVAILABLE_LABEL,
} from "../utils/homeHealth";
import type { LatestVersionResponse, SysHealthData } from "../api/types";

describe("homeHealth", () => {
  it("formats bytes and throughput using readable units", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2_048)).toBe("2.0 KB");
    expect(formatBytes(5_242_880)).toBe("5.0 MB");
    expect(formatBytes(3_221_225_472)).toBe("3.0 GB");
    expect(formatRate(2_048)).toBe("2.0 KB/s");
  });

  it("formats uptime into day/hour/minute groups", () => {
    expect(formatUptime(0)).toBe("0m");
    expect(formatUptime(3_660)).toBe("1h 1m");
    expect(formatUptime(176_400)).toBe("2d 1h");
  });

  it("derives healthy/warning/critical states from telemetry", () => {
    const base: SysHealthData = {
      uptime_seconds: 10,
      cpu: {
        percent_total: 25,
        percent_per_core: [],
        load_avg_1: 0.12,
        load_avg_5: 0.2,
        load_avg_15: 0.3,
      },
      memory: {
        total_bytes: 1,
        used_bytes: 1,
        available_bytes: 0,
        cached_bytes: 0,
        free_bytes: 0,
        used_percent: 40,
      },
      disk: {
        total_bytes: 1,
        used_bytes: 1,
        free_bytes: 0,
        used_percent: 50,
      },
      network: {
        bytes_recv: 1,
        bytes_sent: 1,
        recv_rate_bytes: 1,
        send_rate_bytes: 1,
      },
    };

    expect(deriveSystemHealthStatus(base)).toBe("Healthy");

    expect(
      deriveSystemHealthStatus({
        ...base,
        memory: { ...base.memory, used_percent: 75 },
      }),
    ).toBe("Warning");

    expect(
      deriveSystemHealthStatus({
        ...base,
        disk: { ...base.disk, used_percent: 91 },
      }),
    ).toBe("Critical");

    expect(deriveSystemHealthStatus(null)).toBe(UNAVAILABLE_LABEL);
  });

  it("extracts version number from latest-version response payload", () => {
    const payload: LatestVersionResponse = {
      body: {
        version: {
          version_number: "0.4.7",
        },
      },
    };

    expect(getLatestVersionNumber(payload)).toBe("0.4.7");
    expect(
      getLatestVersionNumber({
        body: {
          Version: {
            VersionNumber: "0.4.8",
          },
        },
      }),
    ).toBe("0.4.8");
    expect(getLatestVersionNumber({})).toBeNull();
  });
});
