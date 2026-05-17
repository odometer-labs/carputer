import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  startTrack,
  endTrack,
  listTracks,
  getTrack,
  updateTrack,
  deleteTrack,
  addTrackPoint,
  getLatestTrackPoint,
  checkNewRoad,
} from "../api/restApi";

beforeEach(() => {
  vi.restoreAllMocks(); // reset mocks before each test
});

describe("restApi", () => {
  it("startTrack returns correct data", async () => {
    // Mock fetch with proper typing
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ create_track: 123 }),
      } as Response),
    ) as typeof fetch;

    const res = await startTrack();
    expect(res.create_track).toBe(123);
  });

  it("endTrack returns correct data", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ result: "success" }),
      } as Response),
    ) as typeof fetch;

    const res = await endTrack();
    expect(res.result).toBe("success");
  });

  it("startTrack throws on bad response", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: false } as Response),
    ) as typeof fetch;

    await expect(startTrack()).rejects.toThrow("Failed to start track");
  });

  it("listTracks returns tracks array", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => [
          { track_id: 1, geom: {}, start_time: "", end_time: "" },
          { track_id: 2, geom: {}, start_time: "", end_time: "" },
        ],
      } as Response),
    ) as typeof fetch;

    const res = await listTracks();

    expect(res).toHaveLength(2);
    expect(res[0]?.track_id).toBe(1);
  });

  it("getTrack returns a single track", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          track_id: 5,
          geom: {},
          start_time: "",
          end_time: "",
        }),
      } as Response),
    ) as typeof fetch;

    const res = await getTrack(5);

    expect(res.track_id).toBe(5);
  });

  it("updateTrack returns success response", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ result: "success" }),
      } as Response),
    ) as typeof fetch;

    const res = await updateTrack(1, {
      end_time: "2026-01-01",
    });

    expect(res.result).toBe("success");
  });

  it("deleteTrack returns success response", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ result: "success" }),
      } as Response),
    ) as typeof fetch;

    const res = await deleteTrack(1);

    expect(res.result).toBe("success");
  });

  it("addTrackPoint sends point correctly", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ result: "success" }),
      } as Response),
    ) as typeof fetch;

    const res = await addTrackPoint({
      latitude: 1,
      longitude: 2,
      speed: 30,
      heading: 90,
    });

    expect(res.result).toBe("success");
  });

  it("getLatestTrackPoint returns latest point", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          point_id: 1,
          track_id: 1,
          time_stamp: "",
          geom: {},
          speed_mph: 30,
          heading_deg: 0,
        }),
      } as Response),
    ) as typeof fetch;

    const res = await getLatestTrackPoint();

    expect(res.point_id).toBe(1);
  });

  it("checkNewRoad returns boolean result", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ is_new_road: true }),
      } as Response),
    ) as typeof fetch;

    const res = await checkNewRoad();

    expect(res.is_new_road).toBe(true);
  });
});
