import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getLatestVersion,
  listTracks,
  subscribeToPositionStream,
} from "../api/restApi";

describe("restApi", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches tracks from the configured list endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [{ track_id: 1 }],
    });

    vi.stubGlobal("fetch", fetchMock);

    const tracks = await listTracks();

    expect(tracks).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/tracks", { method: "GET" });
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
