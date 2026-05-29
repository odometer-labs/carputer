import type { Track } from "../api/types";

export type LonLatCoordinate = [number, number];
export type ImportFileKind = "gpx" | "geojson";

export interface TrackListItem {
  id: number;
  name: string;
  date: string;
  distanceMi: number;
  durationMin: number;
  startPoint: LonLatCoordinate;
  coordinates: LonLatCoordinate[];
}

export const SUPPORTED_IMPORT_EXTENSIONS = [
  ".gpx",
  ".geojson",
  ".json",
] as const;
export const SUPPORTED_IMPORT_HINT =
  "Supported imports: GPX (.gpx) and GeoJSON (.geojson, .json).";

const DEMO_TRACK_SEEDS = [
  {
    id: 9101,
    name: "Morning Loop Demo",
    startTime: "2026-05-20T07:10:00Z",
    endTime: "2026-05-20T07:42:00Z",
    coordinates: [
      [-122.4194, 37.7749],
      [-122.4142, 37.7791],
      [-122.4056, 37.7818],
      [-122.3984, 37.7772],
      [-122.4032, 37.7695],
      [-122.4128, 37.7684],
    ] as LonLatCoordinate[],
  },
  {
    id: 9102,
    name: "Canyon Run Demo",
    startTime: "2026-05-19T16:05:00Z",
    endTime: "2026-05-19T17:21:00Z",
    coordinates: [
      [-105.2705, 40.015],
      [-105.2848, 40.0087],
      [-105.3012, 39.9984],
      [-105.3169, 39.9898],
      [-105.3346, 39.9835],
    ] as LonLatCoordinate[],
  },
  {
    id: 9103,
    name: "Lakefront Demo",
    startTime: "2026-05-18T11:30:00Z",
    endTime: "2026-05-18T12:06:00Z",
    coordinates: [
      [-87.6298, 41.8781],
      [-87.6214, 41.8822],
      [-87.6138, 41.8881],
      [-87.6096, 41.8957],
      [-87.6127, 41.9034],
    ] as LonLatCoordinate[],
  },
  {
    id: 9104,
    name: "Desert Test Demo",
    startTime: "2026-05-17T20:15:00Z",
    endTime: "2026-05-17T21:29:00Z",
    coordinates: [
      [-115.1728, 36.1147],
      [-115.1582, 36.1219],
      [-115.1434, 36.1262],
      [-115.1285, 36.1247],
      [-115.1168, 36.1185],
      [-115.1091, 36.1099],
    ] as LonLatCoordinate[],
  },
];

export function parseTrack(payload: unknown): Track | null {
  if (Array.isArray(payload)) {
    const trackId = Number(payload[0]);
    const geom = payload[1];
    const startTime = typeof payload[2] === "string" ? payload[2] : null;
    const endTime = typeof payload[3] === "string" ? payload[3] : null;
    const trackName = typeof payload[4] === "string" ? payload[4] : null;

    return parseTrack({
      track_id: trackId,
      geom,
      start_time: startTime,
      end_time: endTime,
      track_name: trackName,
    });
  }

  if (typeof payload !== "object" || payload === null) {
    return null;
  }

  const candidate = payload as Record<string, unknown>;
  const trackId = Number(candidate.track_id);
  const startTime =
    typeof candidate.start_time === "string" ? candidate.start_time : null;
  const endTime =
    typeof candidate.end_time === "string" ? candidate.end_time : null;
  const trackName =
    typeof candidate.track_name === "string" ? candidate.track_name : null;

  if (!Number.isFinite(trackId) || !startTime) {
    return null;
  }

  let geom: Track["geom"] = { type: "LineString", coordinates: [] };
  let geometryPayload: unknown = candidate.geom;

  if (typeof geometryPayload === "string") {
    try {
      geometryPayload = JSON.parse(geometryPayload);
    } catch {
      geometryPayload = null;
    }
  }

  if (typeof geometryPayload === "object" && geometryPayload !== null) {
    const geomCandidate = geometryPayload as Record<string, unknown>;
    if (
      geomCandidate.type === "LineString" &&
      Array.isArray(geomCandidate.coordinates)
    ) {
      geom = {
        type: "LineString",
        coordinates: geomCandidate.coordinates
          .filter(
            (coord): coord is [number, number] =>
              Array.isArray(coord) &&
              coord.length >= 2 &&
              Number.isFinite(Number(coord[0])) &&
              Number.isFinite(Number(coord[1])),
          )
          .map((coord) => [Number(coord[0]), Number(coord[1])]),
      };
    }
  }

  return {
    track_id: trackId,
    geom,
    start_time: startTime,
    end_time: endTime,
    track_name: trackName,
  };
}

export function toTrackListItem(track: Track): TrackListItem {
  const coordinates = Array.isArray(track.geom.coordinates)
    ? track.geom.coordinates
    : [];
  const startPoint = coordinates[0] ?? [0, 0];
  const startTime = new Date(track.start_time);
  const endTime = track.end_time ? new Date(track.end_time) : null;

  const durationMin = endTime
    ? Math.max(0, Math.round((endTime.getTime() - startTime.getTime()) / 60000))
    : 0;

  return {
    id: track.track_id,
    name: track.track_name?.trim() || `Track ${track.track_id}`,
    date: track.start_time.split("T")[0] ?? track.start_time,
    distanceMi: calculateDistanceMiles(coordinates),
    durationMin,
    startPoint,
    coordinates,
  };
}

export function normalizeTrackPayload(payload: unknown[]): TrackListItem[] {
  return payload
    .map((track) => parseTrack(track))
    .filter((track): track is Track => track !== null)
    .map((track) => toTrackListItem(track));
}

export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const remainderMinutes = minutes % 60;
  return hours > 0 ? `${hours}h ${remainderMinutes}m` : `${remainderMinutes}m`;
}

export function getImportFileKind(fileName: string): ImportFileKind | null {
  const lowerName = fileName.toLowerCase();

  if (lowerName.endsWith(".gpx")) {
    return "gpx";
  }

  if (lowerName.endsWith(".geojson") || lowerName.endsWith(".json")) {
    return "geojson";
  }

  return null;
}

export function buildDemoTrackItems(): TrackListItem[] {
  return DEMO_TRACK_SEEDS.map((track) => {
    const durationMin = Math.max(
      0,
      Math.round(
        (new Date(track.endTime).getTime() -
          new Date(track.startTime).getTime()) /
          60000,
      ),
    );

    return {
      id: track.id,
      name: track.name,
      date: track.startTime.split("T")[0] ?? track.startTime,
      distanceMi: calculateDistanceMiles(track.coordinates),
      durationMin,
      startPoint: [...track.coordinates[0]] as LonLatCoordinate,
      coordinates: track.coordinates.map(
        (coordinate) => [...coordinate] as LonLatCoordinate,
      ),
    };
  });
}

export function createGpxFromTracks(tracks: TrackListItem[]): string {
  const trackXml = tracks
    .map((track) => {
      const segmentPoints = track.coordinates
        .map(
          ([lon, lat]) => `        <trkpt lat="${lat}" lon="${lon}"></trkpt>`,
        )
        .join("\n");

      return [
        "  <trk>",
        `    <name>${escapeXml(track.name)}</name>`,
        "    <trkseg>",
        segmentPoints,
        "    </trkseg>",
        "  </trk>",
      ].join("\n");
    })
    .join("\n");

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<gpx version="1.1" creator="Carputer Remote Interface" xmlns="http://www.topografix.com/GPX/1/1">',
    trackXml,
    "</gpx>",
  ].join("\n");
}

function escapeXml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function haversineMiles(
  start: LonLatCoordinate,
  end: LonLatCoordinate,
): number {
  const earthRadiusMiles = 3958.7613;
  const toRadians = (degrees: number): number => (degrees * Math.PI) / 180;

  const dLat = toRadians(end[1] - start[1]);
  const dLon = toRadians(end[0] - start[0]);
  const lat1 = toRadians(start[1]);
  const lat2 = toRadians(end[1]);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return earthRadiusMiles * c;
}

function calculateDistanceMiles(coordinates: LonLatCoordinate[]): number {
  if (coordinates.length < 2) return 0;

  let totalDistance = 0;
  for (let index = 1; index < coordinates.length; index += 1) {
    const start = coordinates[index - 1];
    const end = coordinates[index];
    if (!start || !end) continue;
    totalDistance += haversineMiles(start, end);
  }

  return totalDistance;
}
