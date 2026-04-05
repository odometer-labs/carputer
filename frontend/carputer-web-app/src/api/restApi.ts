/*
    this file holds the rest api calls from back end
*/
import type { StartTrackResponse, EndTrackResponse} from "./types";


const API_URL = "http://localhost:8000/v1";

export async function startTrack() : Promise<StartTrackResponse> {
  const res = await fetch(`${API_URL}/tracks-start`, {
    method: "POST"
  });

  if (!res.ok) throw new Error("Failed to start track");

  return await res.json();
}

export async function endTrack() : Promise<EndTrackResponse> {
  const res = await fetch(`${API_URL}/tracks-end`, {
    method: "GET"
  });

  if (!res.ok) throw new Error("Failed to end track");

  return await res.json();
}