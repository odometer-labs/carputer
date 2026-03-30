import { beforeEach, describe, expect, it, vi } from "vitest";
import { get } from "svelte/store";

const STORAGE_KEY = "carputer.preferences.v1";

async function loadPreferencesModule() {
  vi.resetModules();
  return import("../services/preferences");
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

  it("loadPreferences returns defaults when nothing is stored", async () => {
    const { loadPreferences, DEFAULT_PREFERENCES } =
      await loadPreferencesModule();

    expect(loadPreferences()).toEqual(DEFAULT_PREFERENCES);
  });

  it("loadPreferences returns defaults when storage contains malformed JSON", async () => {
    const { loadPreferences, DEFAULT_PREFERENCES } =
      await loadPreferencesModule();
    localStorage.setItem(STORAGE_KEY, "{bad-json");

    expect(loadPreferences()).toEqual(DEFAULT_PREFERENCES);
  });

  it("loadPreferences sanitizes stored values", async () => {
    const { loadPreferences } = await loadPreferencesModule();

    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        toggleSomething: "truthy-string",
        milesToDiscoverRoads: 103,
        nightMode: 0,
        brightness: 8,
        defaultZoom: 30,
        iconSizeLevel: -4,
      }),
    );

    expect(loadPreferences()).toEqual({
      toggleSomething: true,
      milesToDiscoverRoads: 100,
      nightMode: false,
      brightness: 10,
      defaultZoom: 21,
      iconSizeLevel: 1,
    });
  });

  it("savePreferences merges defaults and clamps fields", async () => {
    const { savePreferences, DEFAULT_PREFERENCES } =
      await loadPreferencesModule();

    savePreferences({
      brightness: 200,
      milesToDiscoverRoads: 74,
      defaultZoom: 11,
      iconSizeLevel: 6,
    });

    expect(readStoredPreferences()).toEqual({
      ...DEFAULT_PREFERENCES,
      brightness: 100,
      milesToDiscoverRoads: 75,
      defaultZoom: 12,
      iconSizeLevel: 5,
    });
  });

  it("updatePreferences patches only requested fields", async () => {
    const { preferences, updatePreferences } = await loadPreferencesModule();

    const before = get(preferences);
    updatePreferences({ brightness: 55, nightMode: true });
    const after = get(preferences);

    expect(after.brightness).toBe(55);
    expect(after.nightMode).toBe(true);
    expect(after.toggleSomething).toBe(before.toggleSomething);
    expect(after.milesToDiscoverRoads).toBe(before.milesToDiscoverRoads);
    expect(after.defaultZoom).toBe(before.defaultZoom);
    expect(after.iconSizeLevel).toBe(before.iconSizeLevel);
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
      const { loadPreferences, savePreferences, DEFAULT_PREFERENCES } =
        await loadPreferencesModule();

      expect(loadPreferences()).toEqual(DEFAULT_PREFERENCES);
      expect(() => savePreferences({ brightness: 40 })).not.toThrow();
    } finally {
      if (originalDescriptor) {
        Object.defineProperty(globalThis, "localStorage", originalDescriptor);
      }
    }
  });
});
