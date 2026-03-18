import { writable } from "svelte/store";

export type ErrorSeverity = "non-vital" | "vital";

export interface AppError {
  id: number;
  severity: ErrorSeverity;
  message: string;
  source?: string;
  details?: string;
  timestamp: number;
}

interface AppErrorState {
  fatalError: AppError | null;
  notifications: AppError[];
}

const INITIAL_STATE: AppErrorState = {
  fatalError: null,
  notifications: [],
};

const MAX_NOTIFICATIONS = 4;
const NOTIFICATION_DEDUP_MS = 8000;

const state = writable<AppErrorState>(INITIAL_STATE);

let nextErrorId = 1;
let lastNotificationFingerprint = "";
let lastNotificationAt = 0;

function toMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === "string") {
    return error;
  }

  try {
    return JSON.stringify(error);
  } catch {
    return "Unknown error";
  }
}

function toDetails(error: unknown): string | undefined {
  if (error instanceof Error && error.stack) {
    return error.stack;
  }

  if (typeof error === "string") {
    return undefined;
  }

  try {
    return JSON.stringify(error, null, 2);
  } catch {
    return undefined;
  }
}

function createError(
  severity: ErrorSeverity,
  error: unknown,
  source?: string,
): AppError {
  const now = Date.now();
  return {
    id: nextErrorId++,
    severity,
    message: toMessage(error),
    details: toDetails(error),
    source,
    timestamp: now,
  };
}

function shouldDeduplicateNotification(
  message: string,
  source?: string,
): boolean {
  const fingerprint = `${source ?? "unknown"}|${message}`;
  const now = Date.now();

  if (
    fingerprint === lastNotificationFingerprint &&
    now - lastNotificationAt < NOTIFICATION_DEDUP_MS
  ) {
    return true;
  }

  lastNotificationFingerprint = fingerprint;
  lastNotificationAt = now;
  return false;
}

export function reportNonVitalError(error: unknown, source?: string): void {
  const appError = createError("non-vital", error, source);

  if (shouldDeduplicateNotification(appError.message, appError.source)) {
    return;
  }

  state.update((current) => ({
    ...current,
    notifications: [appError, ...current.notifications].slice(
      0,
      MAX_NOTIFICATIONS,
    ),
  }));
}

export function reportVitalError(error: unknown, source?: string): void {
  const appError = createError("vital", error, source);

  state.update((current) => ({
    ...current,
    fatalError: appError,
  }));
}

export function dismissNonVitalError(errorId: number): void {
  state.update((current) => ({
    ...current,
    notifications: current.notifications.filter((err) => err.id !== errorId),
  }));
}

export function clearVitalError(): void {
  state.update((current) => ({
    ...current,
    fatalError: null,
  }));
}

export function clearAllErrors(): void {
  state.set(INITIAL_STATE);
}

export const appErrorState = {
  subscribe: state.subscribe,
};
