import { describe, it, expect, vi } from "vitest";
import { get } from "svelte/store";
import { trackStore } from "../stores/trackStore";
import * as api from "../api/restApi";

describe("trackStore", () => {
  it("start() sets isTracking and trackId", async () => {
    vi.spyOn(api, "startTrack").mockResolvedValue({ create_track: 42 });

    await trackStore.start();
    const state = get(trackStore);

    expect(state.isTracking).toBe(true);
    expect(state.trackId).toBe(42);
  });

  it("end() resets the isTracking and trackId", async () => {
    vi.spyOn(api, "endTrack").mockResolvedValue({ result: "true" });

    await trackStore.end();
    const state = get(trackStore);

    expect(state.isTracking).toBe(false);
    expect(state.trackId).toBeNull();
  });
});