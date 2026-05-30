import { ENDPOINTS } from "../utils/constants";
import { getLatestVersionNumber } from "../utils/homeHealth";
import type {
  DeleteTrackResponse,
  GPSData,
  LatestVersionResponse,
  SysHealthData,
  ImportTracksResponse,
  Track,
} from "./types";

export async function listTracks(): Promise<Track[]> {
  const res = await fetch(ENDPOINTS.listTracks, {
    method: "GET",
  });

  if (!res.ok) throw new Error("Failed to fetch all tracks");

  const data = (await res.json()) as Track[] | { tracks?: Track[] };
  if (Array.isArray(data)) return data;
  return data.tracks ?? [];
}

export async function deleteTrack(
  trackId: number,
): Promise<DeleteTrackResponse> {
  const res = await fetch(`${ENDPOINTS.deleteTrack}/${trackId}`, {
    method: "DELETE",
  });

  if (!res.ok) throw new Error("Failed to delete track");

  return res.json();
}

export async function importTracksGeoJson(
  geojsonData: unknown,
): Promise<ImportTracksResponse> {
  const res = await fetch(ENDPOINTS.importTracks, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ geojson_data: JSON.stringify(geojsonData) }),
  });

  if (!res.ok) {
    throw new Error(
      await readErrorMessage(res, "Failed to import GeoJSON tracks"),
    );
  }

  return res.json();
}

export async function importTracksGpx(
  file: File,
): Promise<ImportTracksResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(ENDPOINTS.importTracksGpx, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error(await readErrorMessage(res, "Failed to import GPX tracks"));
  }

  return res.json();
}

export async function exportTracksGpx(trackIds: number[]): Promise<Blob> {
  const res = await fetch(ENDPOINTS.exportTracksGpx, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(trackIds),
  });

  if (!res.ok) {
    throw new Error(await readErrorMessage(res, "Failed to export tracks"));
  }

  return res.blob();
}

async function readErrorMessage(
  response: Response,
  fallbackMessage: string,
): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";

  try {
    if (contentType.includes("application/json")) {
      const payload = (await response.json()) as {
        detail?: string;
        message?: string;
      };
      return payload.detail || payload.message || fallbackMessage;
    }

    const text = await response.text();
    return text || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

export async function getLatestVersion(): Promise<string | null> {
  const payload = await fetchJsonWithFallback<LatestVersionResponse>(
    ENDPOINTS.getLatestVersion,
    "Failed to fetch latest version",
    getCoreApiHttpBaseUrl,
  );

  return getLatestVersionNumber(payload);
}

export function subscribeToSysHealth(
  onMessage: (data: SysHealthData) => void,
  onError?: (error: string) => void,
): () => void {
  return subscribeToWebSocket<SysHealthData>(
    getSysHealthWebSocketUrl(),
    getSysHealthWebSocketFallbackUrl,
    parseSysHealthData,
    onMessage,
    onError,
    "sys-health",
  );
}

export function subscribeToPositionStream(
  onMessage: (position: GPSData) => void,
  onError?: (error: string) => void,
): () => void {
  return subscribeToWebSocket<GPSData>(
    getPositionWebSocketUrl(),
    getPositionWebSocketFallbackUrl,
    parseGpsData,
    onMessage,
    onError,
    "GPS",
  );
}

function getCoreApiHttpBaseUrl(): string {
  const env = import.meta.env as Record<string, string | undefined>;
  if (env.VITE_CORE_API_HTTP_URL) {
    return env.VITE_CORE_API_HTTP_URL;
  }

  // In Vite dev (:5173), target the core-api directly on port 8888.
  // In Docker (:3001), route through nginx (/v2/ proxy).
  if (window.location.port === "5173") {
    return `${window.location.protocol}//${window.location.hostname}:8888`;
  }

  return window.location.origin;
}

function getHttpFallbackBaseUrl(primaryBase: string): string | null {
  const sameOriginBase = window.location.origin;
  if (sameOriginBase !== primaryBase) {
    return sameOriginBase;
  }

  return null;
}

async function fetchJsonWithFallback<T>(
  endpoint: string,
  errorMessage: string,
  getBaseUrl: () => string = () => window.location.origin,
): Promise<T> {
  const primaryBase = getBaseUrl();
  const primaryUrl = new URL(endpoint, primaryBase);

  try {
    const primaryRes = await fetch(primaryUrl.toString(), { method: "GET" });
    if (!primaryRes.ok) {
      throw new Error(`Primary request failed: ${primaryRes.status}`);
    }
    return primaryRes.json();
  } catch {
    const fallbackBase = getHttpFallbackBaseUrl(primaryBase);
    if (!fallbackBase) {
      throw new Error(errorMessage);
    }

    const fallbackUrl = new URL(endpoint, fallbackBase);
    const fallbackRes = await fetch(fallbackUrl.toString(), { method: "GET" });
    if (!fallbackRes.ok) {
      throw new Error(errorMessage);
    }

    return fallbackRes.json();
  }
}

function subscribeToWebSocket<T>(
  primaryUrl: string,
  getFallbackUrl: (primaryUrl: string) => string | null,
  parseMessage: (payload: unknown) => T | null,
  onMessage: (data: T) => void,
  onError: ((error: string) => void) | undefined,
  label: string,
): () => void {
  const fallbackUrl = getFallbackUrl(primaryUrl);

  let socket: WebSocket | null = null;
  let hasAttemptedFallback = false;
  let isClosedByCaller = false;

  const tryFallback = (): boolean => {
    if (hasAttemptedFallback || !fallbackUrl || isClosedByCaller) {
      return false;
    }

    hasAttemptedFallback = true;
    connect(fallbackUrl);
    return true;
  };

  const bindHandlers = (ws: WebSocket): void => {
    ws.onmessage = (event: MessageEvent) => {
      try {
        const payload = JSON.parse(event.data);
        const parsed = parseMessage(payload);

        if (!parsed) {
          return;
        }

        onMessage(parsed);
      } catch (error: unknown) {
        if (onError) {
          onError(
            `Failed to parse ${label} websocket payload: ${String(error)}`,
          );
        }
      }
    };

    ws.onerror = () => {
      if (tryFallback()) {
        return;
      }

      if (onError) {
        onError(`${label} websocket connection failed`);
      }
    };

    ws.onclose = () => {
      if (isClosedByCaller) {
        return;
      }

      if (tryFallback()) {
        return;
      }

      if (onError) {
        onError(`${label} websocket connection closed`);
      }
    };
  };

  const connect = (url: string): void => {
    if (
      socket &&
      (socket.readyState === WebSocket.OPEN ||
        socket.readyState === WebSocket.CONNECTING)
    ) {
      socket.close();
    }

    socket = new WebSocket(url);
    bindHandlers(socket);
  };

  connect(primaryUrl);

  return () => {
    isClosedByCaller = true;

    if (
      socket &&
      (socket.readyState === WebSocket.OPEN ||
        socket.readyState === WebSocket.CONNECTING)
    ) {
      socket.close();
    }
  };
}

function getSysHealthWebSocketUrl(): string {
  const env = import.meta.env as Record<string, string | undefined>;
  if (env.VITE_SYS_HEALTH_WS_URL) {
    return env.VITE_SYS_HEALTH_WS_URL;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

  // In Vite dev (:5173), connect directly to sys-health on port 8090.
  // In Docker, route through nginx (/ws/sys-health proxy).
  if (window.location.port === "5173") {
    return `${protocol}//${window.location.hostname}:8090${ENDPOINTS.sysHealthStream}`;
  }

  return `${protocol}//${window.location.host}${ENDPOINTS.sysHealthStream}`;
}

function getSysHealthWebSocketFallbackUrl(primaryUrl: string): string | null {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const sameOriginUrl = `${protocol}//${window.location.host}${ENDPOINTS.sysHealthStream}`;

  if (sameOriginUrl !== primaryUrl) {
    return sameOriginUrl;
  }

  return null;
}

function getPositionWebSocketUrl(): string {
  const env = import.meta.env as Record<string, string | undefined>;
  if (env.VITE_GPS_WS_URL) {
    return env.VITE_GPS_WS_URL;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

  // In dev mode (Vite on :5173), connect directly to the API server on port 8000.
  // In production (port 3001), use the same host and port (proxied through nginx).
  if (window.location.port === "5173") {
    return `${protocol}//${window.location.hostname}:8000${ENDPOINTS.getPositionStream}`;
  }

  return `${protocol}//${window.location.host}${ENDPOINTS.getPositionStream}`;
}

function getPositionWebSocketFallbackUrl(primaryUrl: string): string | null {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const sameOriginUrl = `${protocol}//${window.location.host}${ENDPOINTS.getPositionStream}`;

  if (sameOriginUrl !== primaryUrl) {
    return sameOriginUrl;
  }

  return null;
}

function parseGpsData(payload: unknown): GPSData | null {
  if (typeof payload !== "object" || payload === null) {
    return null;
  }

  const candidate = payload as Record<string, unknown>;
  const latitude = Number(candidate.latitude);
  const longitude = Number(candidate.longitude);
  const speed = Number(candidate.speed);
  const heading = Number(candidate.heading);

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude) ||
    !Number.isFinite(speed) ||
    !Number.isFinite(heading)
  ) {
    return null;
  }

  const isLikelyNoFixPlaceholder =
    latitude === 0 && longitude === 0 && speed === 0 && heading === 0;

  if (isLikelyNoFixPlaceholder) {
    return null;
  }

  return { latitude, longitude, speed, heading };
}

function parseSysHealthData(payload: unknown): SysHealthData | null {
  if (typeof payload !== "object" || payload === null) {
    return null;
  }

  const candidate = payload as SysHealthData;
  const hasTopLevelMetrics =
    typeof candidate.uptime_seconds === "number" &&
    typeof candidate.cpu?.percent_total === "number" &&
    typeof candidate.memory?.used_percent === "number" &&
    typeof candidate.disk?.used_percent === "number";

  if (!hasTopLevelMetrics) {
    return null;
  }

  return candidate;
}
