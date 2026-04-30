<script lang="ts">
  import { onMount } from 'svelte';
  import Map from 'ol/Map.js';
  import View from 'ol/View.js';
  import TileLayer from 'ol/layer/Tile.js';
  import VectorLayer from 'ol/layer/Vector.js';
  import OSM from 'ol/source/OSM.js';
  import VectorSource from 'ol/source/Vector.js';
  import Feature from 'ol/Feature.js';
  import Point from 'ol/geom/Point.js';
  import Style from 'ol/style/Style.js';
  import Stroke from 'ol/style/Stroke.js';
  import CircleStyle from 'ol/style/Circle.js';
  import Fill from 'ol/style/Fill.js';
  import { defaults as defaultControls } from 'ol/control/defaults.js';
  import { fromLonLat } from 'ol/proj.js';
  import type { FeatureLike } from 'ol/Feature.js';
  import 'ol/ol.css';
  import AppBar from '../assets/components/AppBar.svelte';
  import trashcan_icon from '../assets/icons/trash.svg';
  import { deleteTrack, listTracks } from '../api/restApi';
  import type { Track } from '../api/types';
  

  interface TrackListItem {
    id: number;
    name: string;
    date: string;
    distanceMi: number;
    durationMin: number;
    startPoint: LonLatCoordinate;
  }

  type LonLatCoordinate = [number, number];

  const FALLBACK_TRACKS: TrackListItem[] = [
    { id: 1, name: 'Morning Commute', date: '2026-04-13', distanceMi: 8.2, durationMin: 22, startPoint: [-122.4180, 37.7750] },
    { id: 2, name: 'Weekend Drive', date: '2026-04-12', distanceMi: 45.1, durationMin: 74, startPoint: [-122.3321, 47.6062] },
    { id: 3, name: 'Grocery Run', date: '2026-04-11', distanceMi: 3.4, durationMin: 11, startPoint: [-87.6298, 41.8781] },
    { id: 4, name: 'Highway Test', date: '2026-04-10', distanceMi: 120.6, durationMin: 95, startPoint: [-104.9903, 39.7392] },
    { id: 5, name: 'City Loop', date: '2026-04-09', distanceMi: 15.8, durationMin: 38, startPoint: [-74.0060, 40.7128] },
    { id: 6, name: 'Mountain Road', date: '2026-04-08', distanceMi: 62.3, durationMin: 110, startPoint: [-105.2705, 40.0150] },
    { id: 7, name: 'Night Drive', date: '2026-04-07', distanceMi: 28.9, durationMin: 45, startPoint: [-118.2437, 34.0522] },
    { id: 8, name: 'Work Drive', date: '2026-04-08', distanceMi: 15, durationMin: 30, startPoint: [-96.7970, 32.7767] },
    { id: 9, name: 'Joy Ride', date: '2026-04-06', distanceMi: 30, durationMin: 60, startPoint: [-80.1918, 25.7617] },
    { id: 10, name: 'Date Night', date: '2026-04-05', distanceMi: 12, durationMin: 25, startPoint: [-71.0589, 42.3601] },
  ];

  const POINT_VISIBILITY_MIN_ZOOM = 6;

  let mapElement: HTMLDivElement | undefined;
  let map: Map | undefined;
  let trackLayer: VectorLayer<VectorSource> | undefined;
  let searchQuery: string = '';
  let selectedTrackId: number | null = null;
  let filteredTracks: TrackListItem[] = [];

  let tracks: TrackListItem[] = [];

  $: filteredTracks = tracks.filter(t =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.date.includes(searchQuery)
  );

  function getPointStyle(feature: FeatureLike): Style | undefined {
    const currentZoom = map?.getView().getZoom() ?? 0;
    if (currentZoom < POINT_VISIBILITY_MIN_ZOOM) return undefined;

    const featureTrackId = feature.get('trackId') as number | undefined;
    const isSelected = featureTrackId === selectedTrackId;

    return new Style({
      image: new CircleStyle({
        radius: isSelected ? 9 : 6,
        fill: new Fill({ color: isSelected ? '#1565c0' : '#2e7d32' }),
        stroke: new Stroke({ color: '#ffffff', width: 2 })
      })
    });
  }

  function rebuildTrackPoints(): void {
    const source = trackLayer?.getSource();
    if (!source) return;

    source.clear();

    for (const track of tracks) {
      const startFeature = new Feature({
        geometry: new Point(fromLonLat(track.startPoint)),
        trackId: track.id
      });

      source.addFeature(startFeature);
    }
  }

  $: if (trackLayer) {
    tracks;
    rebuildTrackPoints();
  }

  $: if (trackLayer) {
    selectedTrackId;
    trackLayer.changed();
  }

  function formatDuration(minutes: number): string {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }

  function selectTrack(track: TrackListItem): void {
    selectedTrackId = track.id;
    if (!map) return;

    const projectedStart = fromLonLat(track.startPoint);

    map.getView().animate({
      center: projectedStart,
      zoom: 13,
      duration: 650
    });
  }

  let pendingDeleteTrack: TrackListItem | null = null;

  function parseTrack(payload: unknown): Track | null {
    if (Array.isArray(payload)) {
      const trackId = Number(payload[0]);
      const geom = payload[1];
      const startTime = typeof payload[2] === 'string' ? payload[2] : null;
      const endTime = typeof payload[3] === 'string' ? payload[3] : null;

      return parseTrack({
        track_id: trackId,
        geom,
        start_time: startTime,
        end_time: endTime,
      });
    }

    if (typeof payload !== 'object' || payload === null) {
      return null;
    }

    const candidate = payload as Record<string, unknown>;
    const trackId = Number(candidate.track_id);
    const startTime = typeof candidate.start_time === 'string' ? candidate.start_time : null;
    const endTime = typeof candidate.end_time === 'string' ? candidate.end_time : null;

    if (!Number.isFinite(trackId) || !startTime) {
      return null;
    }

    let geom: Track['geom'] = { type: 'LineString', coordinates: [] };
    let geometryPayload: unknown = candidate.geom;

    if (typeof geometryPayload === 'string') {
      try {
        geometryPayload = JSON.parse(geometryPayload);
      } catch {
        geometryPayload = null;
      }
    }

    if (typeof geometryPayload === 'object' && geometryPayload !== null) {
      const geomCandidate = geometryPayload as Record<string, unknown>;
      if (
        geomCandidate.type === 'LineString' &&
        Array.isArray(geomCandidate.coordinates)
      ) {
        geom = {
          type: 'LineString',
          coordinates: geomCandidate.coordinates.filter((coord): coord is [number, number] => (
            Array.isArray(coord) &&
            coord.length >= 2 &&
            Number.isFinite(Number(coord[0])) &&
            Number.isFinite(Number(coord[1]))
          )).map((coord) => [Number(coord[0]), Number(coord[1])]),
        };
      }
    }

    return {
      track_id: trackId,
      geom,
      start_time: startTime,
      end_time: endTime,
    };
  }

  function haversineMiles(start: LonLatCoordinate, end: LonLatCoordinate): number {
    const earthRadiusMiles = 3958.7613;
    const toRadians = (degrees: number): number => (degrees * Math.PI) / 180;

    const dLat = toRadians(end[1] - start[1]);
    const dLon = toRadians(end[0] - start[0]);
    const lat1 = toRadians(start[1]);
    const lat2 = toRadians(end[1]);

    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return earthRadiusMiles * c;
  }

  function calculateDistanceMiles(coordinates: LonLatCoordinate[]): number {
    if (coordinates.length < 2) return 0;

    let totalDistance = 0;
    for (let i = 1; i < coordinates.length; i++) {
      const start = coordinates[i - 1];
      const end = coordinates[i];
      if (!start || !end) continue;
      totalDistance += haversineMiles(start, end);
    }

    return totalDistance;
  }

  function toTrackListItem(track: Track): TrackListItem {
    const coordinates = Array.isArray(track.geom.coordinates) ? track.geom.coordinates : [];
    const startPoint = coordinates[0] ?? [0, 0];
    const startTime = new Date(track.start_time);
    const endTime = track.end_time ? new Date(track.end_time) : null;

    const durationMin = endTime
      ? Math.max(0, Math.round((endTime.getTime() - startTime.getTime()) / 60000))
      : 0;

    return {
      id: track.track_id,
      name: `Track ${track.track_id}`,
      date: track.start_time.split('T')[0] ?? track.start_time,
      distanceMi: calculateDistanceMiles(coordinates),
      durationMin,
      startPoint,
    };
  }

  function useFallbackTracks(): void {
    tracks = FALLBACK_TRACKS.map((track) => ({
      ...track,
      startPoint: [...track.startPoint] as LonLatCoordinate,
    }));
  }

  async function loadTracksFromBackend(): Promise<void> {
    try {
      const payload = await listTracks();
      const parsedTracks = payload
        .map((track) => parseTrack(track))
        .filter((track): track is Track => track !== null)
        .map((track) => toTrackListItem(track));

      if (parsedTracks.length > 0) {
        tracks = parsedTracks;
      } else {
        useFallbackTracks();
      }

      if (selectedTrackId !== null && !parsedTracks.some((track) => track.id === selectedTrackId)) {
        selectedTrackId = null;
      }
    } catch (error: unknown) {
      console.error('Failed to load tracks:', error);
      useFallbackTracks();
    }
  }

  function promptDelete(track: TrackListItem): void {
    pendingDeleteTrack = track;
  }

  async function confirmDelete(): Promise<void> {
    if (!pendingDeleteTrack) return;

    const deletingTrack = pendingDeleteTrack;

    try {
      await deleteTrack(deletingTrack.id);
      tracks = tracks.filter((track) => track.id !== deletingTrack.id);
      if (selectedTrackId === deletingTrack.id) {
        selectedTrackId = null;
      }
      pendingDeleteTrack = null;
    } catch (error: unknown) {
      console.error(`Failed to delete track ${deletingTrack.id}:`, error);
      return;
    }
  }

  function cancelDelete(): void {
    pendingDeleteTrack = null;
  }

  onMount(() => {
    trackLayer = new VectorLayer({
      source: new VectorSource(),
      style: (feature) => getPointStyle(feature)
    });

    map = new Map({
      target: mapElement,
      layers: [
        new TileLayer({ source: new OSM() }),
        trackLayer
      ],
      view: new View({
        center: fromLonLat([0, 0]),
        zoom: 2
      }),
      controls: defaultControls({ rotate: false })
    });

    loadTracksFromBackend();

    map.on('singleclick', (event) => {
      const currentZoom = map?.getView().getZoom() ?? 0;
      if (currentZoom < POINT_VISIBILITY_MIN_ZOOM || !trackLayer) return;

      const clickedFeature = map?.forEachFeatureAtPixel(
        event.pixel,
        (feature, layer) => (layer === trackLayer ? feature : undefined)
      );

      if (!clickedFeature) return;

      const trackId = clickedFeature.get('trackId') as number | undefined;
      if (!trackId) return;

      const clickedTrack = tracks.find((t) => t.id === trackId);
      if (!clickedTrack) return;

      selectedTrackId = clickedTrack.id;
    });

    return () => {
      map?.setTarget(undefined);
      trackLayer = undefined;
    };
  });
</script>

<main class="tracks-shell">
  <AppBar title="Track Viewer" />

  <div class="content-area">
    <!-- Map (left 75%) -->
    <div class="map-container">
      <div bind:this={mapElement} class="map"></div>
    </div>

    <!-- Right panel: search + track list (right 25%) -->
    <div class="right-panel">
      <div class="search-bar-container">
        <input
          class="search-input"
          type="text"
          placeholder="Search tracks..."
          bind:value={searchQuery}
        />
      </div>

      <ul class="track-list">
        {#each filteredTracks as track (track.id)}
          <li
            class="track-list-item"
            class:track-list-item--selected={selectedTrackId === track.id}
          >
            <button
              class="track-item"
              on:click={() => selectTrack(track)}
            >
              <span class="track-name">{track.name}</span>
              <span class="track-meta">{track.date}</span>
              <span class="track-meta">{track.distanceMi.toFixed(1)} mi &bull; {formatDuration(track.durationMin)}</span>
            </button>
            <!-- svelte-ignore a11y_consider_explicit_label -->
            <button
              class="track-delete-btn"
              title="Delete track"
              on:click|stopPropagation={() => promptDelete(track)}
            >
              <img src={trashcan_icon} alt="Trashcan" style="width: 24px; height: 24px;" />
            </button>
          </li>
        {:else}
          <li class="track-empty">No tracks found.</li>
        {/each}
      </ul>
    </div>
  </div>
</main>

{#if pendingDeleteTrack}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="modal-backdrop" on:click={cancelDelete}>
    <div class="modal" on:click|stopPropagation>
      <p class="modal-title">Are you sure you want to delete <strong>{pendingDeleteTrack.name}</strong>? This cannot be undone.</p>
      <div class="modal-actions">
        <button class="modal-btn modal-btn--cancel" on:click={cancelDelete}>Cancel</button>
        <button class="modal-btn modal-btn--confirm" on:click={confirmDelete}>Delete</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .tracks-shell {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--surface-color, #eeeeee);
    color: var(--text-color, #111111);
  }

  .content-area {
    display: flex;
    flex: 1;
    min-height: 0;
  }

  .map-container {
    flex: 1;
    min-width: 0;
  }

  .map {
    width: 100%;
    height: 100%;
  }

  /* Right panel */
  .right-panel {
    width: 25%;
    min-width: 200px;
    display: flex;
    flex-direction: column;
    border-left: 2px solid #000000;
    background: #e0e0e0;
    overflow: hidden;
  }

  .search-bar-container {
    padding: 0.75rem;
    border-bottom: 2px solid #000000;
    flex-shrink: 0;
  }

  .search-input {
    width: 100%;
    box-sizing: border-box;
    padding: 0.5rem 0.75rem;
    border: 1px solid #aaa;
    border-radius: 4px;
    font-size: 0.95rem;
    background: #f5f5f5;
    outline: none;
  }

  .search-input:focus {
    border-color: #555;
    background: #fff;
  }

  /* Track list */
  .track-list {
    flex: 1;
    overflow-y: auto;
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .track-list-item {
    display: flex;
    align-items: stretch;
    border-bottom: 1px solid #c0c0c0;
    transition: background 0.15s;
  }

  .track-list-item:hover {
    background: #d0d0d0;
  }

  .track-list-item--selected {
    background: #b8cce4;
    border-left: 4px solid #3399CC;
  }

  .track-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    padding: 0.75rem 1rem;
    border: none;
    background: transparent;
    cursor: pointer;
    text-align: left;
  }

  .track-delete-btn {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2.5rem;
    border: none;
    border-left: 1px solid #c0c0c0;
    background: transparent;
    color: #888;
    font-size: 0.85rem;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
  }

  .track-delete-btn:hover {
    background: #e57373;
    color: #fff;
  }

  .track-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: #111;
  }

  .track-meta {
    font-size: 0.8rem;
    color: #555;
  }

  .track-empty {
    padding: 1rem;
    color: #888;
    font-size: 0.9rem;
    text-align: center;
  }

  /* Confirmation modal */
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }

  .modal {
    background: var(--secondary-color, rgb(225, 225, 225));
    border: 2px solid #000;
    border-radius: 6px;
    padding: 1rem 1rem;
    max-width: 360px;
    width: 90%;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
  }

  .modal-title {
    margin: 0 0 1rem;
    font-size: 1.15rem;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-start;
    gap: 0.75rem;
  }

  .modal-btn {
    padding: 0.5rem 1.25rem;
    border-radius: 4px;
    border: 1px solid #aaa;
    font-size: 0.9rem;
    cursor: pointer;
    font-weight: 600;
    transition: background 0.15s;
  }

  .modal-btn--cancel {
    background: #e0e0e0;
    color: #333;
  }

  .modal-btn--cancel:hover {
    background: #c8c8c8;
  }

  .modal-btn--confirm {
    background: #c62828;
    color: #fff;
    border-color: #c62828;
  }

  .modal-btn--confirm:hover {
    background: #e57373;
  }

  :global(.ol-zoom button) {
    width: 2.25em;
    height: 2.25em;
    font-size: 1.4rem;
    line-height: 1;
    background-color: rgb(188, 188, 188);
    border: 1px solid white;
  }

  :global(.ol-zoom button:hover) {
    background-color: rgb(225, 225, 225);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
  }
</style>