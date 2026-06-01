import { writable, type Writable } from "svelte/store";

const STORAGE_KEY = "carputer.preferences.v1";

export type TrackRange = "all" | "day" | "week" | "month" | "year";

export interface Preferences {
  areAllTracksOn: boolean;
  areAprsPointsOn: boolean;
  milesToDiscoverRoads: number;
  trackRange: TrackRange;
  selectedTrackColor: string;
  restingTrackColor: string;
  trackThickness: number;
  nightMode: boolean;
  brightness: number;
  defaultZoom: number;
  iconSizeLevel: number;
}

type PreferencesPatch = Partial<Preferences>;

export const DEFAULT_PREFERENCES: Preferences = {
  areAllTracksOn: true,
  areAprsPointsOn: true,
  milesToDiscoverRoads: 50,
  trackRange: "all",
  selectedTrackColor: "#0000ff",
  restingTrackColor: "#008000",
  trackThickness: 4,
  nightMode: false,
  brightness: 100,
  defaultZoom: 18,
  iconSizeLevel: 3,
};

function sanitizeTrackColor(value: unknown, fallback: string): string {
  if (typeof value !== "string") {
    return fallback;
  }

  const normalized = value.trim();
  const hexColorPattern = /^#([0-9a-fA-F]{6})$/;

  if (!hexColorPattern.test(normalized)) {
    return fallback;
  }

  return normalized.toLowerCase();
}

function sanitizeBoolean(value: unknown, fallback: boolean): boolean {
  if (typeof value === "boolean") {
    return value;
  }

  return fallback;
}

function clampMiles(value: unknown): number {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return DEFAULT_PREFERENCES.milesToDiscoverRoads;
  }

  const clamped = Math.min(100, Math.max(0, numericValue));
  return Math.round(clamped / 5) * 5;
}

function clampTrackThickness(value: unknown): number {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return DEFAULT_PREFERENCES.trackThickness;
  }

  return Math.round(Math.min(12, Math.max(1, numericValue)));
}

function clampBrightness(value: unknown): number {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return DEFAULT_PREFERENCES.brightness;
  }

  return Math.round(Math.min(100, Math.max(10, numericValue)));
}

function clampZoom(value: unknown): number {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return DEFAULT_PREFERENCES.defaultZoom;
  }

  return Math.round(Math.min(21, Math.max(12, numericValue)));
}

function clampIconSizeLevel(value: unknown): number {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return DEFAULT_PREFERENCES.iconSizeLevel;
  }

  return Math.round(Math.min(5, Math.max(1, numericValue)));
}

function validateTrackRange(value: unknown): TrackRange {
  switch (value) {
    case "day":
    case "week":
    case "month":
    case "year":
    case "all":
      return value;
    default:
      return DEFAULT_PREFERENCES.trackRange;
  }
}

function sanitizeSettingsPreferences(
  rawPreferences: Partial<Preferences> & { trackColor?: unknown } = {},
): Preferences {
  const hasLegacyTrackColor = typeof rawPreferences.trackColor === "string";
  const legacyTrackColor = hasLegacyTrackColor
    ? sanitizeTrackColor(
        rawPreferences.trackColor,
        DEFAULT_PREFERENCES.selectedTrackColor,
      )
    : null;

  const selectedTrackFallback =
    legacyTrackColor !== null && rawPreferences.selectedTrackColor === undefined
      ? legacyTrackColor
      : DEFAULT_PREFERENCES.selectedTrackColor;

  const restingTrackFallback =
    legacyTrackColor !== null && rawPreferences.restingTrackColor === undefined
      ? legacyTrackColor
      : DEFAULT_PREFERENCES.restingTrackColor;

  return {
    areAllTracksOn: sanitizeBoolean(
      rawPreferences.areAllTracksOn,
      DEFAULT_PREFERENCES.areAllTracksOn,
    ),
    areAprsPointsOn: sanitizeBoolean(
      rawPreferences.areAprsPointsOn,
      DEFAULT_PREFERENCES.areAprsPointsOn,
    ),
    milesToDiscoverRoads: clampMiles(rawPreferences.milesToDiscoverRoads),
    selectedTrackColor: sanitizeTrackColor(
      rawPreferences.selectedTrackColor,
      selectedTrackFallback,
    ),
    restingTrackColor: sanitizeTrackColor(
      rawPreferences.restingTrackColor,
      restingTrackFallback,
    ),
    trackThickness: clampTrackThickness(rawPreferences.trackThickness),
    nightMode: sanitizeBoolean(
      rawPreferences.nightMode,
      DEFAULT_PREFERENCES.nightMode,
    ),
    brightness: clampBrightness(rawPreferences.brightness),
    defaultZoom: clampZoom(rawPreferences.defaultZoom),
    iconSizeLevel: clampIconSizeLevel(rawPreferences.iconSizeLevel),
    trackRange: validateTrackRange(rawPreferences.trackRange),
  };
}

export function loadSettingsPreferences(): Preferences {
  if (typeof localStorage === "undefined") {
    return { ...DEFAULT_PREFERENCES };
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (!stored) {
      return { ...DEFAULT_PREFERENCES };
    }

    const parsed = JSON.parse(stored) as Partial<Preferences>;
    return sanitizeSettingsPreferences(parsed);
  } catch {
    return { ...DEFAULT_PREFERENCES };
  }
}

export function saveSettingsPreferences(
  preferences: Partial<Preferences>,
): void {
  if (typeof localStorage === "undefined") {
    return;
  }

  const sanitized = sanitizeSettingsPreferences({
    ...DEFAULT_PREFERENCES,
    ...preferences,
  });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sanitized));
}

function createSettingsPreferencesStore(): Writable<Preferences> {
  const initialPreferences = loadSettingsPreferences();
  const store = writable<Preferences>(initialPreferences);

  store.subscribe((preferences) => {
    saveSettingsPreferences(preferences);
  });

  return store;
}

export const settingsPreferences = createSettingsPreferencesStore();

export function updateSettingsPreferences(patch: PreferencesPatch): void {
  settingsPreferences.update((currentPreferences) => ({
    ...currentPreferences,
    ...patch,
  }));
}
