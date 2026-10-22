import { describe, it, expect, beforeEach } from "vitest";
import { get } from "svelte/store";
import {
  appErrorState,
  clearAllErrors,
  dismissNonVitalError,
  reportNonVitalError,
  reportVitalError,
} from "../stores/errorStore";

describe("errorStore", () => {
  beforeEach(() => {
    clearAllErrors();
  });

  it("stores non-vital errors as dismissible notifications", () => {
    reportNonVitalError("GPS signal lost", "gps-service");

    const state = get(appErrorState);
    expect(state.notifications).toHaveLength(1);
    const firstNotification = state.notifications[0];
    expect(firstNotification).toBeDefined();
    expect(firstNotification?.severity).toBe("non-vital");

    dismissNonVitalError(firstNotification!.id);
    expect(get(appErrorState).notifications).toHaveLength(0);
  });

  it("stores a vital error as fatal state", () => {
    reportVitalError(new Error("Map renderer crashed"), "home-map-page");

    const state = get(appErrorState);
    expect(state.fatalError).not.toBeNull();
    expect(state.fatalError?.severity).toBe("vital");
    expect(state.fatalError?.message).toContain("Map renderer crashed");
  });

  it("queues non-vital errors and reveals the next after dismiss", () => {
    reportNonVitalError("First warning", "gps-service");
    reportNonVitalError("Second warning", "gps-service");
    reportNonVitalError("Third warning", "gps-service");

    const initial = get(appErrorState).notifications;
    expect(initial).toHaveLength(3);
    expect(initial[0]?.message).toBe("First warning");

    dismissNonVitalError(initial[0]!.id);
    const afterFirstDismiss = get(appErrorState).notifications;
    expect(afterFirstDismiss).toHaveLength(2);
    expect(afterFirstDismiss[0]?.message).toBe("Second warning");

    dismissNonVitalError(afterFirstDismiss[0]!.id);
    const afterSecondDismiss = get(appErrorState).notifications;
    expect(afterSecondDismiss).toHaveLength(1);
    expect(afterSecondDismiss[0]?.message).toBe("Third warning");
  });
});
