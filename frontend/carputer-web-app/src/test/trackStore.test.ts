import { describe, it, expect, vi, beforeEach } from "vitest";
import { get } from "svelte/store";
import { TrackStore } from "../stores/trackStore";
import * as api from "../api/restApi";
import type { Track } from "../api/types";

describe("TrackStore", () => {
  let store: TrackStore;

  beforeEach(() => {
    store = new TrackStore();
    vi.restoreAllMocks();
  });

  it("start() sets isTracking and trackId", async () => {
    vi.spyOn(api, "startTrack").mockResolvedValue({ create_track: 42 });

    await store.start();
    const state = get(store);

    expect(state.isTracking).toBe(true);
    expect(state.trackId).toBe(42);
  });

  it("end() resets isTracking and trackId", async () => {
    vi.spyOn(api, "endTrack").mockResolvedValue({
      result: "true",
    });

    await store.end();
    const state = get(store);

    expect(state.isTracking).toBe(false);
    expect(state.trackId).toBeNull();
  });

  it("loadTracks() filters out unfinished tracks", async () => {
    const mockTracks: Track[] = [
      {
        track_id: 1,
        geom: { type: "LineString", coordinates: [] },
        start_time: "2024-01-01T00:00:00Z",
        end_time: "2024-01-01T01:00:00Z",
      },
      {
        track_id: 2,
        geom: { type: "LineString", coordinates: [] },
        start_time: "2024-01-01T00:00:00Z",
        end_time: null,
      },
    ];

    vi.spyOn(api, "listTracks").mockResolvedValue(mockTracks);

    await store.loadTracks();
    const state = get(store);

    const first = state.tracks[0];
    expect(first).toBeDefined();
    expect(first!.track_id).toBe(1);
  });

  it("selectTrack() toggles selectedTrackId", () => {
    store.selectTrack(5);
    let state = get(store);
    expect(state.selectedTrackId).toBe(5);

    // toggle off
    store.selectTrack(5);
    state = get(store);
    expect(state.selectedTrackId).toBeNull();
  });

  
  it("setTrack() overwrites tracks", () => {
    const mockTracks: Track[] = [
      {
        track_id: 10,
        geom: { type: "LineString", coordinates: [] },
        start_time: "2024-01-01T00:00:00Z",
        end_time: "2024-01-01T01:00:00Z",
      },
    ];

    store.setTrack(mockTracks);
    const state = get(store);

    expect(state.tracks).toEqual(mockTracks);
  });

  it("checkIfNewRoad() updates isOnNewRoad", async () => {
    vi.spyOn(api, "checkNewRoad").mockResolvedValue({
      is_new_road: true,
    });

    await store.checkIfNewRoad();
    const state = get(store);

    expect(state.isOnNewRoad).toBe(true);
  });
});