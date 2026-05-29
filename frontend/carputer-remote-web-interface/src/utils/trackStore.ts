import { derived, get, writable } from "svelte/store";
import { listTracks } from "../api/restApi";
import type { TrackListItem } from "./trackData";
import { buildDemoTrackItems, normalizeTrackPayload } from "./trackData";

interface TrackLoadState {
  isLoading: boolean;
  error: string | null;
  usingDemoData: boolean;
}

const trackItemsStore = writable<TrackListItem[]>([]);
const trackLoadStateStore = writable<TrackLoadState>({
  isLoading: false,
  error: null,
  usingDemoData: false,
});
const exportQueueStore = writable<number[]>([]);

export const trackItems = {
  subscribe: trackItemsStore.subscribe,
};

export const trackLoadState = {
  subscribe: trackLoadStateStore.subscribe,
};

export const exportTrackIds = {
  subscribe: exportQueueStore.subscribe,
};

export const exportTracks = derived(
  [trackItemsStore, exportQueueStore],
  ([$trackItemsStore, $exportQueueStore]) =>
    $trackItemsStore.filter((track) => $exportQueueStore.includes(track.id)),
);

export const exportTrackCount = derived(
  exportQueueStore,
  ($exportQueueStore) => $exportQueueStore.length,
);

export async function loadTracksFromApi(): Promise<void> {
  trackLoadStateStore.set({ isLoading: true, error: null });

  try {
    const payload = await listTracks();
    const normalizedTracks = normalizeTrackPayload(payload);

    if (normalizedTracks.length > 0) {
      trackItemsStore.set(normalizedTracks);
      pruneExportQueue(normalizedTracks);
      trackLoadStateStore.set({
        isLoading: false,
        error: null,
        usingDemoData: false,
      });
      return;
    }

    const demoTracks = buildDemoTrackItems();
    trackItemsStore.set(demoTracks);
    pruneExportQueue(demoTracks);
    trackLoadStateStore.set({
      isLoading: false,
      error: null,
      usingDemoData: true,
    });
  } catch (error: unknown) {
    const demoTracks = buildDemoTrackItems();
    trackItemsStore.set(demoTracks);
    pruneExportQueue(demoTracks);
    trackLoadStateStore.set({
      isLoading: false,
      error:
        error instanceof Error
          ? `${error.message} Showing demo tracks for UI testing.`
          : "Failed to load tracks. Showing demo tracks for UI testing.",
      usingDemoData: true,
    });
  }
}

export function toggleTrackQueued(trackId: number): void {
  exportQueueStore.update((trackIds) =>
    trackIds.includes(trackId)
      ? trackIds.filter((id) => id !== trackId)
      : [...trackIds, trackId],
  );
}

export function removeTrackFromStores(trackId: number): void {
  trackItemsStore.update((tracks) =>
    tracks.filter((track) => track.id !== trackId),
  );
  removeTrackFromExportQueue(trackId);
}

export function removeTrackFromExportQueue(trackId: number): void {
  exportQueueStore.update((trackIds) =>
    trackIds.filter((id) => id !== trackId),
  );
}

export function clearExportQueue(): void {
  exportQueueStore.set([]);
}

export function isTrackQueued(trackId: number): boolean {
  return get(exportQueueStore).includes(trackId);
}

function pruneExportQueue(tracks: TrackListItem[]): void {
  const validTrackIds = new Set(tracks.map((track) => track.id));
  exportQueueStore.update((trackIds) =>
    trackIds.filter((trackId) => validTrackIds.has(trackId)),
  );
}
