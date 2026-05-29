import { ENDPOINTS } from "../utils/constants";
import type { DeleteTrackResponse, ImportTracksResponse } from "./types";

export async function listTracks(): Promise<unknown[]> {
  const res = await fetch(ENDPOINTS.listTracks, {
    method: "GET",
  });

  if (!res.ok) throw new Error("Failed to fetch all tracks");

  return res.json();
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
    body: JSON.stringify(geojsonData),
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
