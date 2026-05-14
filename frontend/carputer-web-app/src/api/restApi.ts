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
  APRSStation,
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

  return res.json();
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
  track: Partial<Track>,
): Promise<UpdateTrackResponse> {
  const res = await fetch(`${ENDPOINTS.getTrack}/${trackId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(track),
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
  trackId: number,
  point: TrackPoint,
): Promise<AddTrackPointResponse> {
  const res = await fetch(`${ENDPOINTS.addTrackPoint}/${trackId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(point),
  });

  if (!res.ok) throw new Error("Failed to add track point");

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
  const res = await fetch(ENDPOINTS.getCurrentPosition, {
    method: "GET",
  });

  if (!res.ok) throw new Error("Failed to fetch current GPS position");

  return res.json();
}

// subscribes to backend websocket stream of live GPS data.
export function subscribeToPositionStream(
  onMessage: (position: GPSData) => void,
  onError?: (error: string) => void,
): () => void {
  const ws = new WebSocket(getPositionWebSocketUrl());

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
    if (onError) onError("GPS websocket connection failed");
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

// fetches APRS stations near the current GPS position.
export async function getAprsStations(
  radiusM: number = 50000,
): Promise<APRSStation[]> {
  const url = new URL(ENDPOINTS.getAprsStations, window.location.origin);
  url.searchParams.set("radius_m", String(radiusM));
  const res = await fetch(url.toString(), { method: "GET" });

  if (!res.ok) throw new Error("Failed to fetch APRS stations");

  return res.json();
}
