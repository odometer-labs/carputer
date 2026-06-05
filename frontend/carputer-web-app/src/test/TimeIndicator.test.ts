import { describe, it, expect } from "vitest";
import { formatTime } from "../utils/dateUtils";

// testing the function formatTime with example times to check formating.
describe("formatTime", () => {
  it("formats night correctly", () => {
    const date = new Date(2025, 0, 1, 0, 5); // 12:05
    expect(formatTime(date)).toBe("12:05 AM");
  });

  it("formats morning correctly", () => {
    const date = new Date(2024, 0, 1, 9, 4); // 9:04
    expect(formatTime(date)).toBe("9:04 AM");
  });

  it("formats afternoon correctly", () => {
    const date = new Date(2004, 0, 1, 12, 30); // 12:30
    expect(formatTime(date)).toBe("12:30 PM");
  });

  it("formats minutes with a 0 infront when single digits", () => {
    const date = new Date(2024, 0, 1, 1, 4); // 1:04
    expect(formatTime(date)).toBe("1:04 AM");
  });
});