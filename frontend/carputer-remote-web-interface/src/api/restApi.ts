import { ENDPOINTS } from "../utils/constants";
import type { DeleteTrackResponse } from "./types";

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
