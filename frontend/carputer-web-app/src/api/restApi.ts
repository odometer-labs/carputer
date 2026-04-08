/*
    this file holds the rest api calls from back end
*/
import type { StartTrackResponse, EndTrackResponse} from "./types";
import { ENDPOINTS } from "../utils/constants";


export async function startTrack() : Promise<StartTrackResponse> {
  const res = await fetch(ENDPOINTS.startTrack, {
    method: "POST"
  });

  if (!res.ok) throw new Error("Failed to start track");

  return await res.json();
}

export async function endTrack() : Promise<EndTrackResponse> {
  const res = await fetch(ENDPOINTS.endTrack, {
    method: "GET"
  });

  if (!res.ok) throw new Error("Failed to end track");

  return await res.json();
}