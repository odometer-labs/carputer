import { beforeEach, describe, expect, it, vi } from "vitest";
import { get } from "svelte/store";

const STORAGE_KEY = "carputer.preferences.v1";

async function loadSettingsPreferencesModule() {
  vi.resetModules();
  return import("../services/settings_preferences");
}

function readStoredPreferences() {
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : null;
}

describe("preferences service", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("loadSettingsPreferences returns defaults when nothing is stored", async () => {
    const { loadSettingsPreferences, DEFAULT_PREFERENCES } =
      await loadSettingsPreferencesModule();

    expect(loadSettingsPreferences()).toEqual(DEFAULT_PREFERENCES);
  });

  it("loadSettingsPreferences returns defaults when storage contains malformed JSON", async () => {
    const { loadSettingsPreferences, DEFAULT_PREFERENCES } =
      await loadSettingsPreferencesModule();
    localStorage.setItem(STORAGE_KEY, "{bad-json");

    expect(loadSettingsPreferences()).toEqual(DEFAULT_PREFERENCES);
  });

  it("loadSettingsPreferences sanitizes stored values", async () => {
    const { loadSettingsPreferences, DEFAULT_PREFERENCES } =
      await loadSettingsPreferencesModule();

    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        areAllTracksOn: "truthy-string",
        milesToDiscoverRoads: 103,
        selectedTrackColor: "not-a-color",
        restingTrackColor: "also-bad",
        trackThickness: 99,
        nightMode: 0,
        brightness: 8,
        defaultZoom: 30,
        iconSizeLevel: -4,
        trackRange: "banan",
      }),
    );

    expect(loadSettingsPreferences()).toEqual({
      areAllTracksOn: true,
      areAprsPointsOn: true,
      milesToDiscoverRoads: 100,
      selectedTrackColor: DEFAULT_PREFERENCES.selectedTrackColor,
      restingTrackColor: DEFAULT_PREFERENCES.restingTrackColor,
      trackThickness: 12,
      nightMode: false,
      brightness: 10,
      defaultZoom: 21,
      iconSizeLevel: 1,
      trackRange: "all",
    });
  });

  it("saveSettingsPreferences merges defaults and clamps fields", async () => {
    const { saveSettingsPreferences, DEFAULT_PREFERENCES } =
      await loadSettingsPreferencesModule();

    saveSettingsPreferences({
      brightness: 200,
      milesToDiscoverRoads: 74,
      selectedTrackColor: "#00FF99",
      restingTrackColor: "#3355aa",
      trackThickness: 0,
      defaultZoom: 11,
      iconSizeLevel: 6,
    });

    expect(readStoredPreferences()).toEqual({
      ...DEFAULT_PREFERENCES,
      brightness: 100,
      milesToDiscoverRoads: 75,
      selectedTrackColor: "#00ff99",
      restingTrackColor: "#3355aa",
      trackThickness: 1,
      defaultZoom: 12,
      iconSizeLevel: 5,
      trackRange: "all",
    });
  });

  it("updateSettingsPreferences patches only requested fields", async () => {
    const { settingsPreferences, updateSettingsPreferences } =
      await loadSettingsPreferencesModule();

    const before = get(settingsPreferences);
    updateSettingsPreferences({ brightness: 55, nightMode: true });
    const after = get(settingsPreferences);

    expect(after.brightness).toBe(55);
    expect(after.nightMode).toBe(true);
    expect(after.areAllTracksOn).toBe(before.areAllTracksOn);
    expect(after.areAprsPointsOn).toBe(before.areAprsPointsOn);
    expect(after.milesToDiscoverRoads).toBe(before.milesToDiscoverRoads);
    expect(after.selectedTrackColor).toBe(before.selectedTrackColor);
    expect(after.restingTrackColor).toBe(before.restingTrackColor);
    expect(after.trackThickness).toBe(before.trackThickness);
    expect(after.defaultZoom).toBe(before.defaultZoom);
    expect(after.iconSizeLevel).toBe(before.iconSizeLevel);
  });

  it("sanitizes selected/resting track colors to 6-digit hex values", async () => {
    const {
      saveSettingsPreferences,
      loadSettingsPreferences,
      DEFAULT_PREFERENCES,
    } = await loadSettingsPreferencesModule();

    saveSettingsPreferences({
      selectedTrackColor: "#12abEF",
      restingTrackColor: "#ABCDEF",
    });
    expect(loadSettingsPreferences().selectedTrackColor).toBe("#12abef");
    expect(loadSettingsPreferences().restingTrackColor).toBe("#abcdef");

    saveSettingsPreferences({
      selectedTrackColor: "#abc",
      restingTrackColor: "invalid",
    });
    expect(loadSettingsPreferences().selectedTrackColor).toBe(
      DEFAULT_PREFERENCES.selectedTrackColor,
    );
    expect(loadSettingsPreferences().restingTrackColor).toBe(
      DEFAULT_PREFERENCES.restingTrackColor,
    );
  });

  it("migrates legacy trackColor to selected and resting colors", async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        trackColor: "#2277CC",
      }),
    );

    const { loadSettingsPreferences } = await loadSettingsPreferencesModule();

    expect(loadSettingsPreferences().selectedTrackColor).toBe("#2277cc");
    expect(loadSettingsPreferences().restingTrackColor).toBe("#2277cc");
  });

  it("sanitizes trackThickness into supported range", async () => {
    const { saveSettingsPreferences, loadSettingsPreferences } =
      await loadSettingsPreferencesModule();

    saveSettingsPreferences({ trackThickness: 7 });
    expect(loadSettingsPreferences().trackThickness).toBe(7);

    saveSettingsPreferences({ trackThickness: 20 });
    expect(loadSettingsPreferences().trackThickness).toBe(12);
  });

  it("safe no-op behavior when localStorage is unavailable", async () => {
    const originalDescriptor = Object.getOwnPropertyDescriptor(
      globalThis,
      "localStorage",
    );

    Object.defineProperty(globalThis, "localStorage", {
      value: undefined,
      configurable: true,
    });

    try {
      const {
        loadSettingsPreferences,
        saveSettingsPreferences,
        DEFAULT_PREFERENCES,
      } = await loadSettingsPreferencesModule();

      expect(loadSettingsPreferences()).toEqual(DEFAULT_PREFERENCES);
      expect(() => saveSettingsPreferences({ brightness: 40 })).not.toThrow();
    } finally {
      if (originalDescriptor) {
        Object.defineProperty(globalThis, "localStorage", originalDescriptor);
      }
    }
  });

  it("handles trackRange correctly", async () => {
    const { saveSettingsPreferences, loadSettingsPreferences } =
      await loadSettingsPreferencesModule();

    saveSettingsPreferences({
      trackRange: "day",
    });

    expect(loadSettingsPreferences().trackRange).toBe("day");
  });
});
