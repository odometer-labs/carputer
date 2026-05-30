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
  import type { Track } from '../api/types';
  import { trackStore, selectedTrack } from '../stores/trackStore';
  import LineString from 'ol/geom/LineString.js';
  

  interface TrackListItem {
    id: number;
    name: string;
    date: string;
    distanceMi: number;
    durationMin: number;
    startPoint: LonLatCoordinate;
  }

  type LonLatCoordinate = [number, number];

  const POINT_VISIBILITY_MIN_ZOOM = 6;

  let mapElement: HTMLDivElement | undefined;
  let map: Map | undefined;
  let pointLayer: VectorLayer<VectorSource> | undefined;
  let routeLayer: VectorLayer<VectorSource> | undefined;
  let searchQuery: string = '';
  let selectedTrackId: number | null = null;
  let filteredTracks: TrackListItem[] = [];

  let tracks: TrackListItem[] = [];

  $: filteredTracks = tracks.filter(t =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.date.includes(searchQuery)
  );

  $: tracks = $trackStore.tracks.map(toTrackListItem);
  $: selectedTrackId = $selectedTrack?.track_id ?? null;

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

  //line routes style
  function getRouteStyle(feature: FeatureLike): Style {
    return new Style({
      stroke: new Stroke({
        color: '#1565c0',
        width: 5 
      })
    });
  }

  function rebuildTrackPoints(): void {
    const source = pointLayer?.getSource();
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

  // rebuild the track route when seleted
  function rebuildRoutes(): void {
    const source = routeLayer?.getSource();

    if (!source) return;

    source.clear();

    const track = $selectedTrack;

    if (!track) return;

    if (!track.geom || !Array.isArray(track.geom.coordinates)) {
      return;
    }

    const projectedCoords = track.geom.coordinates.map(coord =>
      fromLonLat(coord)
    );

    const feature = new Feature({
      geometry: new LineString(projectedCoords),
      trackId: track.track_id
    });

    source.addFeature(feature);
  }

  $: if (pointLayer) {
    tracks;
    rebuildTrackPoints();
  }

  $: if (routeLayer) {
    $selectedTrack;
    rebuildRoutes();
  }

  $: if (pointLayer) {
    selectedTrackId;
    pointLayer.changed();
  }

  function formatDuration(minutes: number): string {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }

  function selectTrack(track: TrackListItem): void {
    //incase the track is already selected then you can't unselect it.
    if ($selectedTrack?.track_id === track.id) {
      return;
    }

    trackStore.selectTrack(track.id);

    if (!map) return;

    const rawTrack = $trackStore.tracks.find(t =>
      t.track_id === track.id
    );

    if (!rawTrack) return;

    const projectedCoords = rawTrack.geom.coordinates.map(coord =>
      fromLonLat(coord)
    );

    const trackLine = new LineString(projectedCoords);

    map.getView().fit(trackLine.getExtent(), {
      padding: [50, 50, 50, 50],
      duration: 650,
      maxZoom: 15
    })
  }

  let pendingDeleteTrack: TrackListItem | null = null;

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
      name: track.track_name ?? `Track ${track.track_id}`,//it should have a name but just incase
      date: track.start_time.split('T')[0] ?? track.start_time,
      distanceMi: calculateDistanceMiles(coordinates),
      durationMin,
      startPoint,
    };
  }

  function promptDelete(track: TrackListItem): void {
    pendingDeleteTrack = track;
  }

  async function confirmDelete(): Promise<void> {
    if (!pendingDeleteTrack) return;

    const deletingTrack = pendingDeleteTrack;

    try {
      await trackStore.deleteTrack(deletingTrack.id);
      if (selectedTrackId === deletingTrack.id) {
        selectedTrackId = null;
      }
      pendingDeleteTrack = null;
    } catch (error: unknown) {
      return;
    }
  }

  function cancelDelete(): void {
    pendingDeleteTrack = null;
  }

  onMount(() => {
    trackStore.loadTracks();

    pointLayer = new VectorLayer({
      source: new VectorSource(),
      style: (feature) => getPointStyle(feature)
    });

    routeLayer = new VectorLayer({
      source: new VectorSource(),
      style: (feature) => getRouteStyle(feature)
    });

    map = new Map({
      target: mapElement,
      layers: [
        new TileLayer({ source: new OSM() }),
        routeLayer,
        pointLayer
      ],
      view: new View({
        center: fromLonLat([0, 0]),
        zoom: 2
      }),
      controls: defaultControls({ rotate: false })
    });

    map.on('singleclick', (event) => {
      const currentZoom = map?.getView().getZoom() ?? 0;
      if (currentZoom < POINT_VISIBILITY_MIN_ZOOM || !pointLayer) return;

      const clickedFeature = map?.forEachFeatureAtPixel(
        event.pixel,
        (feature, layer) => (layer === pointLayer ? feature : undefined)
      );

      if (!clickedFeature) return;

      const trackId = clickedFeature.get('trackId') as number | undefined;
      if (!trackId) return;

      const clickedTrack = tracks.find((t) => t.id === trackId);
      if (!clickedTrack) return;

      selectTrack(clickedTrack);
    });

    return () => {
      map?.setTarget(undefined);
      pointLayer = undefined;
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