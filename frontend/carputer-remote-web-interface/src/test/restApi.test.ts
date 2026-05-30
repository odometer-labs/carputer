import { afterEach, describe, expect, it, vi } from "vitest";
import {
  deleteTrack,
  exportTracksGpx,
  getLatestVersion,
  importTracksGeoJson,
  importTracksGpx,
  listTracks,
  subscribeToPositionStream,
} from "../api/restApi";

describe("restApi", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("listTracks targets /v2/tracks/list-tracks and unwraps the tracks field", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        tracks: [
          {
            track_id: 1,
            geom: { type: "LineString", coordinates: [] },
            start_time: "2026-05-20T07:10:00Z",
            end_time: "2026-05-20T07:42:00Z",
            track_name: "Morning Loop",
          },
        ],
      }),
    });

    vi.stubGlobal("fetch", fetchMock);

    const tracks = await listTracks();

    expect(tracks).toHaveLength(1);
    expect(tracks[0]?.track_name).toBe("Morning Loop");
    expect(fetchMock).toHaveBeenCalledWith("/v2/tracks/list-tracks", {
      method: "GET",
    });
  });

  it("listTracks returns an empty array when the v2 payload omits tracks", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    vi.stubGlobal("fetch", fetchMock);

    const tracks = await listTracks();

    expect(tracks).toEqual([]);
  });

  it("listTracks still tolerates a bare-array response (legacy fallback)", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [
        {
          track_id: 7,
          geom: { type: "LineString", coordinates: [] },
          start_time: "2026-05-20T07:10:00Z",
          end_time: null,
        },
      ],
    });

    vi.stubGlobal("fetch", fetchMock);

    const tracks = await listTracks();

    expect(tracks).toHaveLength(1);
    expect(tracks[0]?.track_id).toBe(7);
  });

  it("listTracks throws when the response is not ok", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false });
    vi.stubGlobal("fetch", fetchMock);

    await expect(listTracks()).rejects.toThrow("Failed to fetch all tracks");
  });

  it("deleteTrack targets /v2/tracks/{id} with DELETE", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ result: "success" }),
    });

    vi.stubGlobal("fetch", fetchMock);

    await deleteTrack(42);

    expect(fetchMock).toHaveBeenCalledWith("/v2/tracks/42", {
      method: "DELETE",
    });
  });

  it("deleteTrack throws when the response is not ok", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false });
    vi.stubGlobal("fetch", fetchMock);

    await expect(deleteTrack(9)).rejects.toThrow("Failed to delete track");
  });

  it("importTracksGeoJson targets /v2/tracks/import-track with a {geojson_data} envelope", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 5 }),
    });

    vi.stubGlobal("fetch", fetchMock);

    const geojson = {
      type: "LineString",
      coordinates: [
        [-122.4194, 37.7749],
        [-122.4142, 37.7791],
      ],
    };

    await importTracksGeoJson(geojson);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/v2/tracks/import-track");
    expect(init.method).toBe("POST");
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe(
      "application/json",
    );

    const parsedBody = JSON.parse(init.body as string) as {
      geojson_data: string;
    };
    expect(typeof parsedBody.geojson_data).toBe("string");
    expect(JSON.parse(parsedBody.geojson_data)).toEqual(geojson);
  });

  it("importTracksGeoJson surfaces the backend error message when present", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "invalid geojson" }),
    });

    vi.stubGlobal("fetch", fetchMock);

    await expect(importTracksGeoJson({})).rejects.toThrow("invalid geojson");
  });

  it("importTracksGpx still targets the legacy v1 endpoint with multipart form data", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ result: "success" }),
    });

    vi.stubGlobal("fetch", fetchMock);

    const file = new File([new Uint8Array([1, 2, 3])], "trip.gpx", {
      type: "application/gpx+xml",
    });

    await importTracksGpx(file);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/tracks/import/gpx");
    expect(init.method).toBe("POST");
    expect(init.body).toBeInstanceOf(FormData);
    expect((init.body as FormData).get("file")).toBe(file);
  });

  it("exportTracksGpx still targets the legacy v1 endpoint with a JSON id list", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(["<gpx />"], { type: "application/gpx+xml" }),
    });

    vi.stubGlobal("fetch", fetchMock);

    const blob = await exportTracksGpx([1, 2, 3]);

    expect(blob).toBeInstanceOf(Blob);
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/tracks/export/gpx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify([1, 2, 3]),
    });
  });

  it("fetches and parses latest version from the core API endpoint", async () => {
    Object.defineProperty(globalThis, "window", {
      value: {
        location: {
          protocol: "http:",
          hostname: "localhost",
          host: "localhost:5173",
          origin: "http://localhost:5173",
          port: "5173",
        },
      },
      configurable: true,
    });

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        body: {
          version: {
            version_number: "0.5.0",
          },
        },
      }),
    });

    vi.stubGlobal("fetch", fetchMock);

    const version = await getLatestVersion();

    expect(version).toBe("0.5.0");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8888/v2/versioning/latest",
      { method: "GET" },
    );
  });

  it("ignores all-zero GPS placeholder websocket messages", () => {
    class MockWebSocket {
      static OPEN = 1;
      static CONNECTING = 0;
      static lastInstance: MockWebSocket | null = null;

      readyState = MockWebSocket.OPEN;
      onmessage: ((event: MessageEvent) => void) | null = null;
      onerror: (() => void) | null = null;
      onclose: (() => void) | null = null;

      constructor(_url: string) {
        MockWebSocket.lastInstance = this;
      }

      close() {
        this.readyState = 3;
      }
    }

    Object.defineProperty(globalThis, "window", {
      value: {
        location: {
          protocol: "http:",
          hostname: "localhost",
          host: "localhost:5173",
          origin: "http://localhost:5173",
          port: "5173",
        },
      },
      configurable: true,
    });

    vi.stubGlobal("WebSocket", MockWebSocket as unknown as typeof WebSocket);

    const onMessage = vi.fn();
    const stop = subscribeToPositionStream(onMessage);
    const wsInstance = MockWebSocket.lastInstance as unknown as WebSocket;

    wsInstance.onmessage?.({
      data: JSON.stringify({
        latitude: 0,
        longitude: 0,
        speed: 0,
        heading: 0,
      }),
    } as MessageEvent);

    expect(onMessage).not.toHaveBeenCalled();

    wsInstance.onmessage?.({
      data: JSON.stringify({
        latitude: 47.6097,
        longitude: -122.3331,
        speed: 3.5,
        heading: 90,
      }),
    } as MessageEvent);

    expect(onMessage).toHaveBeenCalledWith({
      latitude: 47.6097,
      longitude: -122.3331,
      speed: 3.5,
      heading: 90,
    });

    stop();
  });
});
