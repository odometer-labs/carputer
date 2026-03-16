import { writable, type Writable } from "svelte/store";

const STORAGE_KEY = "carputer.preferences.v1";

export interface Preferences {
  toggleSomething: boolean;
  milesToDiscoverRoads: number;
  nightMode: boolean;
  brightness: number;
  defaultZoom: number;
  iconSizeLevel: number;
}

type PreferencesPatch = Partial<Preferences>;

export const DEFAULT_PREFERENCES: Preferences = {
  toggleSomething: false,
  milesToDiscoverRoads: 50,
  nightMode: false,
  brightness: 100,
  defaultZoom: 18,
  iconSizeLevel: 3,
};

function clampMiles(value: unknown): number {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return DEFAULT_PREFERENCES.milesToDiscoverRoads;
  }

  const clamped = Math.min(100, Math.max(0, numericValue));
  return Math.round(clamped / 5) * 5;
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

function sanitizePreferences(
  rawPreferences: Partial<Preferences> = {},
): Preferences {
  return {
    toggleSomething: Boolean(rawPreferences.toggleSomething),
    milesToDiscoverRoads: clampMiles(rawPreferences.milesToDiscoverRoads),
    nightMode: Boolean(rawPreferences.nightMode),
    brightness: clampBrightness(rawPreferences.brightness),
    defaultZoom: clampZoom(rawPreferences.defaultZoom),
    iconSizeLevel: clampIconSizeLevel(rawPreferences.iconSizeLevel),
  };
}

export function loadPreferences(): Preferences {
  if (typeof localStorage === "undefined") {
    return { ...DEFAULT_PREFERENCES };
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (!stored) {
      return { ...DEFAULT_PREFERENCES };
    }

    const parsed = JSON.parse(stored) as Partial<Preferences>;
    return sanitizePreferences({ ...DEFAULT_PREFERENCES, ...parsed });
  } catch {
    return { ...DEFAULT_PREFERENCES };
  }
}

export function savePreferences(preferences: Partial<Preferences>): void {
  if (typeof localStorage === "undefined") {
    return;
  }

  const sanitized = sanitizePreferences({
    ...DEFAULT_PREFERENCES,
    ...preferences,
  });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sanitized));
}

function createPreferencesStore(): Writable<Preferences> {
  const initialPreferences = loadPreferences();
  const store = writable<Preferences>(initialPreferences);

  store.subscribe((preferences) => {
    savePreferences(preferences);
  });

  return store;
}

export const preferences = createPreferencesStore();

export function updatePreferences(patch: PreferencesPatch): void {
  preferences.update((currentPreferences) => ({
    ...currentPreferences,
    ...patch,
  }));
}
