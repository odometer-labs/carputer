import { describe, expect, it } from "vitest";
import { parseSystemLog } from "../utils/logs";

describe("parseSystemLog", () => {
  it("groups Python log lines into severity buckets", () => {
    const parsed = parseSystemLog(
      [
        "2026-04-28 18:31:00,101 - handlers.py:12 - INFO: Logger initialized",
        "2026-04-28 18:32:00,101 - track_client.py:44 - WARNING: GPS signal degraded",
        "2026-04-28 18:33:00,101 - main.py:19 - ERROR: Failed to write point to database",
      ].join("\n"),
    );

    expect(parsed.total).toBe(3);
    expect(parsed.errors).toHaveLength(1);
    expect(parsed.warnings).toHaveLength(1);
    expect(parsed.messages).toHaveLength(1);
    expect(parsed.errors[0]?.message).toContain("Failed to write point");
    expect(parsed.warnings[0]?.source).toBe("track_client.py:44");
    expect(parsed.messages[0]?.level).toBe("INFO");
  });

  it("falls back to message severity for unstructured lines", () => {
    const parsed = parseSystemLog("Service started without structured logging");

    expect(parsed.total).toBe(1);
    expect(parsed.messages).toHaveLength(1);
    expect(parsed.messages[0]?.message).toBe(
      "Service started without structured logging",
    );
  });

  it("falls back to message severity for unstructured lines even when they contain severity keywords", () => {
    const parsed = parseSystemLog(
      [
        "WARNING: unstructured warning line",
        "ERROR: unstructured error line",
        "CRITICAL: unstructured critical line",
      ].join("\n"),
    );

    expect(parsed.total).toBe(3);
    expect(parsed.messages).toHaveLength(3);
    expect(parsed.errors).toHaveLength(0);
    expect(parsed.warnings).toHaveLength(0);
  });
});
