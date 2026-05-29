import { writable, derived } from 'svelte/store';
import { listTracks, deleteTrack } from '../api/restApi';
import type { Track } from '../api/types';

interface RemoteTracksState {
  tracks: Track[];
  selectedTrackId: number | null;
  loading: boolean;
  error: string | null;
}

function createTrackStore() {
  const store = writable<RemoteTracksState>({
    tracks: [],
    selectedTrackId: null,
    loading: false,
    error: null
  });

  const { subscribe, update } = store;

  return {
    subscribe,

    async loadTracks(): Promise<void> {
      update(state => ({
        ...state,
        loading: true,
        error: null
      }));

      try {
        const tracks = await listTracks();

        const finishedTracks = tracks
          .filter(track => track.end_time != null)
          .sort(
            (a, b) =>
              new Date(b.start_time).getTime() -
              new Date(a.start_time).getTime()
          );

        update(state => ({
          ...state,
          tracks: finishedTracks,
          loading: false
        }));
      } catch (error) {
        console.error(error);

        update(state => ({
          ...state,
          loading: false,
          error: 'Failed to load tracks'
        }));
      }
    },

    selectTrack(trackId: number): void {
      update(state => ({
        ...state,
        selectedTrackId:
          state.selectedTrackId === trackId
            ? null
            : trackId
      }));
    },

    clearSelection(): void {
      update(state => ({
        ...state,
        selectedTrackId: null
      }));
    },

    async deleteTrack(trackId: number): Promise<void> {
      try {
        await deleteTrack(trackId);

        update(state => ({
          ...state,

          tracks: state.tracks.filter(
            track => track.track_id !== trackId
          ),

          selectedTrackId:
            state.selectedTrackId === trackId
              ? null
              : state.selectedTrackId
        }));
      } catch (error) {
        console.error(error);

        update(state => ({
          ...state,
          error: 'Failed to delete track'
        }));
      }
    }
  };
}

export const trackStore = createTrackStore();

export const selectedTrack = derived(
  trackStore,
  ($trackStore) =>
    $trackStore.tracks.find(
      track => track.track_id === $trackStore.selectedTrackId
    ) ?? null
);