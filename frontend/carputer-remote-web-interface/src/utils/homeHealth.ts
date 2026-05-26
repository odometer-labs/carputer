import type { LatestVersionResponse, SysHealthData } from "../api/types";

export const UNAVAILABLE_LABEL = "Unavailable";

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) {
    return "0B";
  }

  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
  if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(1)} MB`;
  if (bytes >= 1_024) return `${(bytes / 1_024).toFixed(1)} KB`;
  return `${Math.round(bytes)} B`;
}

export function formatRate(bytesPerSecond: number): string {
  return `${formatBytes(bytesPerSecond)}/s`;
}

export function formatUptime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return "0m";
  }

  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);

  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function deriveSystemHealthStatus(
  sysHealth: SysHealthData | null,
): string {
  if (!sysHealth) {
    return UNAVAILABLE_LABEL;
  }

  const maxUsage = Math.max(
    sysHealth.cpu.percent_total,
    sysHealth.memory.used_percent,
    sysHealth.disk.used_percent,
  );

  if (maxUsage >= 90) {
    return "Critical";
  }

  if (maxUsage >= 70) {
    return "Warning";
  }

  return "Healthy";
}

export function getLatestVersionNumber(
  payload: LatestVersionResponse,
): string | null {
  const versionNumber = payload.body?.version?.version_number;
  if (typeof versionNumber === "string" && versionNumber.trim().length > 0) {
    return versionNumber;
  }

  return null;
}
