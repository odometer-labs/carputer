/*
    this file holds the rest api calls from back end
*/
import type {
  StartTrackResponse,
  EndTrackResponse,
  Track,
  UpdateTrackResponse,
  DeleteTrackResponse,
  TrackPoint,
  AddTrackPointResponse,
  LatestTrackPoint,
  CheckNewRoadResponse,
  GPSData,
  SysHealthData,
  APRSStation,
  ImportTrackResponse,
  LineString,
  Region,
  RegionDataModel,
  UpdateTrackVal,
} from "./types";
import { ENDPOINTS } from "../utils/constants";

// starts a new track in the database
export async function startTrack(): Promise<StartTrackResponse> {
  const res = await fetch(ENDPOINTS.startTrack, {
    method: "POST",
  });

  if (!res.ok) throw new Error("Failed to start track");

  return res.json();
}

// ends a current active track in the database
export async function endTrack(): Promise<EndTrackResponse> {
  const res = await fetch(ENDPOINTS.endTrack, {
    method: "GET",
  });

  if (!res.ok) throw new Error("Failed to end track");

  return res.json();
}

// fetches all tracks, which have atleast one geom point
export async function listTracks(): Promise<Track[]> {
  const res = await fetch(ENDPOINTS.listTracks, {
    method: "GET",
  });

  if (!res.ok) throw new Error("Failed to fetch all tracks");

  const data = await res.json();
  return data.tracks ?? [];
}

// fetches a specific track, could be used if the user is looking for a specific track
export async function getTrack(trackId: number): Promise<Track> {
  const res = await fetch(`${ENDPOINTS.getTrack}/${trackId}`, {
    method: "GET",
  });

  if (!res.ok) throw new Error("Failed to fetch a tracks");

  return res.json();
}

// updates a specified track by id.
export async function updateTrack(
  trackId: number,
  trackVal: UpdateTrackVal,
): Promise<UpdateTrackResponse> {
  const res = await fetch(`${ENDPOINTS.getTrack}/${trackId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(trackVal),
  });

  if (!res.ok) throw new Error("Failed to update a track");

  return res.json();
}

// this will delete a track by it's track id
export async function deleteTrack(
  trackId: number,
): Promise<DeleteTrackResponse> {
  const res = await fetch(`${ENDPOINTS.deleteTrack}/${trackId}`, {
    method: "DELETE",
  });

  if (!res.ok) throw new Error("Failed to delete a track");

  return res.json();
}

// this usese the track id and a track point(latitude, longitude, speed, and heading)
export async function addTrackPoint(
  point: TrackPoint,
): Promise<AddTrackPointResponse> {
  const res = await fetch(`${ENDPOINTS.addTrackPoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(point),
  });

  if (!res.ok) throw new Error("Failed to add track point");

  return res.json();
}

// imports a full geojson track into backend
export async function importTrack(
  geojson: LineString,
): Promise<ImportTrackResponse> {
  const res = await fetch(`${ENDPOINTS.addTrack}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ geojson_data: JSON.stringify(geojson) }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Failed to import track: ${errorText}`);
  }

  return res.json();
}

// this should get the last track point made I believe
export async function getLatestTrackPoint(): Promise<LatestTrackPoint> {
  const res = await fetch(`${ENDPOINTS.getLatestTrackPoint}`, {
    method: "GET",
  });

  if (!res.ok) throw new Error("Failed to fetch a track point");

  return res.json();
}

// the should fetch if the road currently on is a new road or not.
export async function checkNewRoad(): Promise<CheckNewRoadResponse> {
  const res = await fetch(ENDPOINTS.checkNewRoad);

  if (!res.ok) throw new Error("Failed to check for new road");

  return res.json();
}

// gets the most recent position snapshot from the backend.
export async function getCurrentPosition(): Promise<GPSData> {
  return fetchJsonWithFallback<GPSData>(
    ENDPOINTS.getCurrentPosition,
    "Failed to fetch current GPS position",
    undefined,
    getCoreApiHttpBaseUrl,
  );
}

function getCoreApiHttpBaseUrl(): string {
  const env = import.meta.env as Record<string, string | undefined>;
  if (env.VITE_CORE_API_HTTP_URL) {
    return env.VITE_CORE_API_HTTP_URL;
  }

  // In Docker (:3000) and Vite dev (:5173), target the core-api directly.
  if (window.location.port === "3000" || window.location.port === "5173") {
    return `${window.location.protocol}//${window.location.hostname}:8888`;
  }

  return window.location.origin;
}

function getApiHttpBaseUrl(): string {
  const env = import.meta.env as Record<string, string | undefined>;
  if (env.VITE_API_HTTP_URL) {
    return env.VITE_API_HTTP_URL;
  }

  // In Docker frontend (:3000) and Vite dev (:5173), target the API directly.
  if (window.location.port === "3000" || window.location.port === "5173") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }

  return window.location.origin;
}

function getApiHttpFallbackBaseUrl(primaryBase: string): string | null {
  const sameOriginBase = window.location.origin;
  if (sameOriginBase !== primaryBase) {
    return sameOriginBase;
  }

  return null;
}

async function fetchJsonWithFallback<T>(
  endpoint: string,
  errorMessage: string,
  searchParams?: Record<string, string>,
  getBaseUrl: () => string = getApiHttpBaseUrl,
): Promise<T> {
  const primaryBase = getBaseUrl();
  const primaryUrl = new URL(endpoint, primaryBase);
  if (searchParams) {
    Object.entries(searchParams).forEach(([key, value]) => {
      primaryUrl.searchParams.set(key, value);
    });
  }

  try {
    const primaryRes = await fetch(primaryUrl.toString(), { method: "GET" });
    if (!primaryRes.ok) {
      throw new Error(`Primary request failed: ${primaryRes.status}`);
    }
    return primaryRes.json();
  } catch {
    const fallbackBase = getApiHttpFallbackBaseUrl(primaryBase);
    if (!fallbackBase) {
      throw new Error(errorMessage);
    }

    const fallbackUrl = new URL(endpoint, fallbackBase);
    if (searchParams) {
      Object.entries(searchParams).forEach(([key, value]) => {
        fallbackUrl.searchParams.set(key, value);
      });
    }

    const fallbackRes = await fetch(fallbackUrl.toString(), { method: "GET" });
    if (!fallbackRes.ok) {
      throw new Error(errorMessage);
    }

    return fallbackRes.json();
  }
}

// subscribes to backend websocket stream of live GPS data.
export function subscribeToPositionStream(
  onMessage: (position: GPSData) => void,
  onError?: (error: string) => void,
): () => void {
  const primaryUrl = getPositionWebSocketUrl();
  const fallbackUrl = getPositionWebSocketFallbackUrl(primaryUrl);

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
        const raw = JSON.parse(event.data);
        const latitude = Number(raw.latitude);
        const longitude = Number(raw.longitude);
        const heading = Number(raw.heading);
        const speed = Number(raw.speed);

        if (
          !Number.isFinite(latitude) ||
          !Number.isFinite(longitude) ||
          !Number.isFinite(heading) ||
          !Number.isFinite(speed)
        ) {
          return;
        }

        onMessage({ latitude, longitude, heading, speed });
      } catch (error: unknown) {
        if (onError)
          onError(`Failed to parse GPS websocket payload: ${String(error)}`);
      }
    };

    ws.onerror = () => {
      if (tryFallback()) {
        return;
      }

      if (onError) {
        onError("GPS websocket connection failed");
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
        onError("GPS websocket connection closed");
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

export function subscribeToSysHealth(
  onMessage: (data: SysHealthData) => void,
  onError?: (error: string) => void,
): () => void {
  const ws = new WebSocket(getSysHealthWebSocketUrl());

  ws.onmessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data) as SysHealthData;
      onMessage(data);
    } catch (error: unknown) {
      if (onError)
        onError(`Failed to parse sys-health payload: ${String(error)}`);
    }
  };

  ws.onerror = () => {
    if (onError) onError("sys-health websocket connection failed");
  };

  return () => {
    if (
      ws.readyState === WebSocket.OPEN ||
      ws.readyState === WebSocket.CONNECTING
    ) {
      ws.close();
    }
  };
}

function getSysHealthWebSocketUrl(): string {
  const env = import.meta.env as Record<string, string | undefined>;
  if (env.VITE_SYS_HEALTH_WS_URL) {
    return env.VITE_SYS_HEALTH_WS_URL;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

  if (window.location.port === "5173") {
    return `${protocol}//${window.location.hostname}:8090${ENDPOINTS.sysHealthStream}`;
  }

  return `${protocol}//${window.location.host}${ENDPOINTS.sysHealthStream}`;
}

function getPositionWebSocketUrl(): string {
  const env = import.meta.env as Record<string, string | undefined>;
  if (env.VITE_GPS_WS_URL) {
    return env.VITE_GPS_WS_URL;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

  // In dev mode (Vite on :5173) or Docker frontend (nginx on :3000), connect
  // directly to the API server on port 8000 — the API port is always exposed
  // to the host in docker-compose, so this bypasses any nginx WebSocket proxy issues.
  if (window.location.port === "5173" || window.location.port === "3000") {
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

// fetches APRS stations near the current GPS position.
export async function getAprsStations(
  radiusM: number = 50000,
): Promise<APRSStation[] | null> {
  const primaryBase = getCoreApiHttpBaseUrl();
  const primaryUrl = new URL(ENDPOINTS.getAprsStations, primaryBase);

  const fetchOptions: RequestInit = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ meters: radiusM }),
  };

  try {
    const primaryRes = await fetch(primaryUrl.toString(), fetchOptions);
    if (!primaryRes.ok) {
      throw new Error(`Primary request failed: ${primaryRes.status}`);
    }
    const data = await primaryRes.json();
    return data.aprs_stations ?? null;
  } catch {
    const fallbackBase = getApiHttpFallbackBaseUrl(primaryBase);
    if (!fallbackBase) {
      throw new Error("Failed to fetch APRS stations");
    }

    const fallbackUrl = new URL(ENDPOINTS.getAprsStations, fallbackBase);
    const fallbackRes = await fetch(fallbackUrl.toString(), fetchOptions);
    if (!fallbackRes.ok) {
      throw new Error("Failed to fetch APRS stations");
    }
    const data = await fallbackRes.json();
    return data.aprs_stations ?? null;
  }
}

// creates a new persisted region in core-api.
export async function createRegion(region: Region): Promise<void> {
  const primaryBase = getCoreApiHttpBaseUrl();
  const primaryUrl = new URL(ENDPOINTS.region, primaryBase);

  const fetchOptions: RequestInit = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(region),
  };

  try {
    const primaryRes = await fetch(primaryUrl.toString(), fetchOptions);
    if (!primaryRes.ok) {
      throw new Error(`Primary request failed: ${primaryRes.status}`);
    }
    return;
  } catch {
    const fallbackBase = getApiHttpFallbackBaseUrl(primaryBase);
    if (!fallbackBase) {
      throw new Error("Failed to create region");
    }

    const fallbackUrl = new URL(ENDPOINTS.region, fallbackBase);
    const fallbackRes = await fetch(fallbackUrl.toString(), fetchOptions);
    if (!fallbackRes.ok) {
      throw new Error("Failed to create region");
    }
  }
}

// fetches all persisted regions from core-api.
export async function listRegions(): Promise<RegionDataModel[]> {
  const primaryBase = getCoreApiHttpBaseUrl();
  const primaryUrl = new URL(ENDPOINTS.region, primaryBase);

  try {
    const primaryRes = await fetch(primaryUrl.toString(), { method: "GET" });
    if (!primaryRes.ok) {
      throw new Error(`Primary request failed: ${primaryRes.status}`);
    }
    const data = await primaryRes.json();
    return data.regions ?? [];
  } catch {
    const fallbackBase = getApiHttpFallbackBaseUrl(primaryBase);
    if (!fallbackBase) {
      throw new Error("Failed to list regions");
    }

    const fallbackUrl = new URL(ENDPOINTS.region, fallbackBase);
    const fallbackRes = await fetch(fallbackUrl.toString(), { method: "GET" });
    if (!fallbackRes.ok) {
      throw new Error("Failed to list regions");
    }
    const data = await fallbackRes.json();
    return data.regions ?? [];
  }
}

// deletes a persisted region by id.
export async function deleteRegion(id: number): Promise<void> {
  const primaryBase = getCoreApiHttpBaseUrl();
  const primaryUrl = new URL(ENDPOINTS.region, primaryBase);

  const fetchOptions: RequestInit = {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  };

  try {
    const primaryRes = await fetch(primaryUrl.toString(), fetchOptions);
    if (!primaryRes.ok) {
      throw new Error(`Primary request failed: ${primaryRes.status}`);
    }
    return;
  } catch {
    const fallbackBase = getApiHttpFallbackBaseUrl(primaryBase);
    if (!fallbackBase) {
      throw new Error("Failed to delete region");
    }

    const fallbackUrl = new URL(ENDPOINTS.region, fallbackBase);
    const fallbackRes = await fetch(fallbackUrl.toString(), fetchOptions);
    if (!fallbackRes.ok) {
      throw new Error("Failed to delete region");
    }
  }
}

//gets the current version/patch level of the application
export async function getLatestVersion(): Promise<LatestVersionResponse> {
  const version = await fetchJsonWithFallback<LatestVersionResponse>(
    ENDPOINTS.getLatestVersion,
    "Failed to fetch latest version",
    undefined,
    getCoreApiHttpBaseUrl,
  );

  return version;
}
