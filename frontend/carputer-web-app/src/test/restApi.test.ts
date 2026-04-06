import { describe, it, expect, vi, beforeEach } from "vitest";
import { startTrack, endTrack } from "../api/restApi";

beforeEach(() => {
  vi.restoreAllMocks(); // reset mocks before each test
});

describe("restApi", () => {
  it("startTrack returns correct data", async () => {
    // Mock fetch with proper typing
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ createdTrackId: 123 }),
      } as Response)
    ) as typeof fetch;

    const res = await startTrack();
    expect(res.createdTrackId).toBe(123);
  });

  it("endTrack returns correct data", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ success: "true" }),
      } as Response)
    ) as typeof fetch;

    const res = await endTrack();
    expect(res.success).toBe("true");
  });

  it("startTrack throws on bad response", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: false } as Response)
    ) as typeof fetch;

    await expect(startTrack()).rejects.toThrow("Failed to start track");
  });
});