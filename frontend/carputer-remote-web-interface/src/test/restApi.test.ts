import { afterEach, describe, expect, it, vi } from "vitest";
import { getLatestVersion, listTracks } from "../api/restApi";

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
});
