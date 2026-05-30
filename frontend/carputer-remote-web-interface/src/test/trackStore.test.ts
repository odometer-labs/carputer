import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { trackStore, selectedTrack } from '../stores/trackStore';
import * as restApi from '../api/restApi';
import type { Track } from '../api/types';

// mock the REST API module
vi.mock('../api/restApi', () => ({
  listTracks: vi.fn(),
  deleteTrack: vi.fn()
}));

const mockTracks: Track[] = [
  {
    track_id: 1,
    start_time: '2026-05-01T10:00:00Z',
    end_time: '2026-05-01T11:00:00Z',
    geom: {
      type: 'LineString',
      coordinates: [
        [-122.0, 47.0],
        [-122.1, 47.1]
      ]
    }
  },
  {
    track_id: 2,
    start_time: '2026-05-03T10:00:00Z',
    end_time: '2026-05-03T11:00:00Z',
    geom: {
      type: 'LineString',
      coordinates: [
        [-123.0, 48.0],
        [-123.1, 48.1]
      ]
    }
  },
  {
    // unfinished track (should be filtered out)
    track_id: 3,
    start_time: '2026-05-04T10:00:00Z',
    end_time: null,
    geom: {
      type: 'LineString',
      coordinates: []
    }
  }
] as Track[];

describe('trackStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads and filters finished tracks', async () => {
    vi.mocked(restApi.listTracks).mockResolvedValue(mockTracks);

    await trackStore.loadTracks();

    const state = get(trackStore);

    expect(state.loading).toBe(false);

    // unfinished track removed
    expect(state.tracks).toHaveLength(2);

    // newest first
    expect(state.tracks[0]?.track_id).toBe(2);
    expect(state.tracks[1]?.track_id).toBe(1);
  });

  it('selects and unselects a track', () => {
    trackStore.selectTrack(1);

    expect(get(trackStore).selectedTrackId).toBe(1);

    // make it so that you selected it off
    trackStore.selectTrack(1);

    expect(get(trackStore).selectedTrackId).toBeNull();
  });

  it('clears selection', () => {
    trackStore.selectTrack(2);

    expect(get(trackStore).selectedTrackId).toBe(2);

    // make it so that you have nothing selected
    trackStore.clearSelection();

    expect(get(trackStore).selectedTrackId).toBeNull();
  });

  it('deletes a track', async () => {
    vi.mocked(restApi.listTracks).mockResolvedValue(mockTracks);

    await trackStore.loadTracks();

    vi.mocked(restApi.deleteTrack).mockResolvedValue({});

    await trackStore.deleteTrack(1);

    const state = get(trackStore);

    expect(state.tracks).toHaveLength(1);
    expect(state.tracks[0]?.track_id).toBe(2);
    });

  it('updates selectedTrack derived store', async () => {
    vi.mocked(restApi.listTracks).mockResolvedValue(mockTracks);

    await trackStore.loadTracks();

    trackStore.selectTrack(2);

    const selected = get(selectedTrack);

    expect(selected?.track_id).toBe(2);
  });

  it('handles loadTracks failure', async () => {
    vi.mocked(restApi.listTracks).mockRejectedValue(
      new Error('API failure')
    );

    await trackStore.loadTracks();

    const state = get(trackStore);

    expect(state.loading).toBe(false);
    expect(state.error).toBe('Failed to load tracks');
  });
});