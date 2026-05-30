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
  importTrack,
  getCurrentPosition,
} from "../api/restApi";

function stubWindowLocation(port: string = "5173") {
  Object.defineProperty(globalThis, "window", {
    value: {
      location: {
        protocol: "http:",
        hostname: "localhost",
        host: `localhost:${port}`,
        origin: `http://localhost:${port}`,
        port,
      },
    },
    configurable: true,
  });
}

beforeEach(() => {
  vi.restoreAllMocks(); // reset mocks before each test
});

describe("restApi", () => {
  it("startTrack returns correct data", async () => {
    // Mock fetch with proper typing
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ id: 123 }),
      } as Response),
    ) as unknown as typeof fetch;
    global.fetch = fetchMock;

    const res = await startTrack();
    expect(res.id).toBe(123);
    expect(fetchMock).toHaveBeenCalledWith("/v2/tracks", { method: "POST" });
  });

  it("endTrack returns correct data", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({}),
      } as Response),
    ) as unknown as typeof fetch;
    global.fetch = fetchMock;

    await endTrack(); // v2 returns empty body, just confirm it resolves
    expect(fetchMock).toHaveBeenCalledWith("/v2/tracks", { method: "GET" });
  });

  it("startTrack throws on bad response", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: false } as Response),
    ) as typeof fetch;

    await expect(startTrack()).rejects.toThrow("Failed to start track");
  });

  it("listTracks returns tracks array", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          tracks: [
            { track_id: 1, geom: {}, start_time: "", end_time: "" },
            { track_id: 2, geom: {}, start_time: "", end_time: "" },
          ],
        }),
      } as Response),
    ) as unknown as typeof fetch;
    global.fetch = fetchMock;

    const res = await listTracks();

    expect(res).toHaveLength(2);
    expect(res[0]?.track_id).toBe(1);
    expect(fetchMock).toHaveBeenCalledWith("/v2/tracks/list-tracks", {
      method: "GET",
    });
  });

  it("listTracks returns empty array when v2 payload omits tracks", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({}),
      } as Response),
    ) as typeof fetch;

    const res = await listTracks();
    expect(res).toEqual([]);
  });

  it("getTrack returns a single track", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          track_id: 5,
          geom: {},
          start_time: "",
          end_time: "",
        }),
      } as Response),
    ) as unknown as typeof fetch;
    global.fetch = fetchMock;

    const res = await getTrack(5);

    expect(res.track_id).toBe(5);
    expect(fetchMock).toHaveBeenCalledWith("/v2/tracks/5", { method: "GET" });
  });

  it("updateTrack returns success response", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({}),
      } as Response),
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await updateTrack(1, {
      start_time: "2002",
      end_time: "2026-01-01",
      track_name: "non",
    });

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/v2/tracks/1");
    expect(init.method).toBe("PUT");
    expect(JSON.parse(init.body as string)).toEqual({
      start_time: "2002",
      end_time: "2026-01-01",
      track_name: "non",
    });
  });

  it("deleteTrack returns success response", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({}),
      } as Response),
    ) as unknown as typeof fetch;
    global.fetch = fetchMock;

    await deleteTrack(1);
    expect(fetchMock).toHaveBeenCalledWith("/v2/tracks/1", {
      method: "DELETE",
    });
  });

  it("addTrackPoint sends point correctly", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({}),
      } as Response),
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await addTrackPoint({
      latitude: 1,
      longitude: 2,
      speed: 30,
      heading: 90,
    });

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/v2/tracks/track-point");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      latitude: 1,
      longitude: 2,
      speed: 30,
      heading: 90,
    });
  });

  it("getLatestTrackPoint returns latest point", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          point_id: 1,
          track_id: 1,
          time_stamp: "",
          geom: {},
          speed_mps: 30,
          heading_deg: 0,
        }),
      } as Response),
    ) as unknown as typeof fetch;
    global.fetch = fetchMock;

    const res = await getLatestTrackPoint();

    expect(res.point_id).toBe(1);
    expect(res.speed_mps).toBe(30);
    expect(fetchMock).toHaveBeenCalledWith("/v2/tracks/latest-track-point", {
      method: "GET",
    });
  });

  it("checkNewRoad returns boolean result", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ is_new_road: true }),
      } as Response),
    ) as unknown as typeof fetch;
    global.fetch = fetchMock;

    const res = await checkNewRoad();

    expect(res.is_new_road).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith("/v2/tracks/check-new-road");
  });

  it("importTrack wraps GeoJSON in the v2 {geojson_data} envelope", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ track_id: 9 }),
      } as Response),
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    const geojson = {
      type: "LineString" as const,
      coordinates: [
        [-122.4194, 37.7749],
        [-122.4142, 37.7791],
      ] as [number, number][],
    };

    await importTrack(geojson);

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/v2/tracks/import-track");
    expect(init.method).toBe("POST");
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe(
      "application/json",
    );

    const parsed = JSON.parse(init.body as string) as {
      geojson_data: string;
    };
    expect(typeof parsed.geojson_data).toBe("string");
    expect(JSON.parse(parsed.geojson_data)).toEqual(geojson);
  });

  it("getCurrentPosition targets the core-api /v2/position endpoint", async () => {
    stubWindowLocation("5173");

    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          latitude: 47.6097,
          longitude: -122.3331,
          speed: 3.5,
          heading: 90,
        }),
      } as Response),
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    const pos = await getCurrentPosition();

    expect(pos).toEqual({
      latitude: 47.6097,
      longitude: -122.3331,
      speed: 3.5,
      heading: 90,
    });

    const [calledUrl, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(calledUrl).toBe("http://localhost:8888/v2/position");
    expect(init.method).toBe("GET");
  });
});
