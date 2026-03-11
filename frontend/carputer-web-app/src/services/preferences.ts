const STORAGE_KEY = "carputer.preferences.v1";

export interface Preferences {
  toggleSomething: boolean;
  milesToDiscoverRoads: number;
  nightMode: boolean;
}

export const DEFAULT_PREFERENCES: Preferences = {
  toggleSomething: false,
  milesToDiscoverRoads: 50,
  nightMode: false,
};

function clampMiles(value: unknown): number {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return DEFAULT_PREFERENCES.milesToDiscoverRoads;
  }

  const clamped = Math.min(100, Math.max(0, numericValue));
  return Math.round(clamped / 5) * 5;
}

function sanitizePreferences(
  rawPreferences: Partial<Preferences> = {},
): Preferences {
  return {
    toggleSomething: Boolean(rawPreferences.toggleSomething),
    milesToDiscoverRoads: clampMiles(rawPreferences.milesToDiscoverRoads),
    nightMode: Boolean(rawPreferences.nightMode),
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
