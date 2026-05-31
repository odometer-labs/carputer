<script lang="ts">
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
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
  import export_add_icon from '../assets/icons/page-plus.svg';
  import export_remove_icon from '../assets/icons/page-minus.svg';
  import { deleteTrack } from '../api/restApi';
  import {
    exportTrackCount,
    exportTrackIds,
    loadTracksFromApi,
    removeTrackFromStores,
    trackItems,
    trackLoadState,
    toggleTrackQueued,
  } from '../utils/trackStore';
  import { formatDuration, type TrackListItem } from '../utils/trackData';
  import LineString from 'ol/geom/LineString.js'
  import { boundingExtent } from 'ol/extent';

  const POINT_VISIBILITY_MIN_ZOOM = 6;

  let mapElement: HTMLDivElement | undefined;
  let map: Map | undefined;
  let trackLayer: VectorLayer<VectorSource> | undefined;
  let trackLineLayer: VectorLayer<VectorSource> | undefined;
  let searchQuery: string = '';
  let selectedTrackId: number | null = null;
  let filteredTracks: TrackListItem[] = [];
  let pageError: string | null = null;
  let isDeleting: boolean = false;

  $: filteredTracks = $trackItems.filter(t =>
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

  //line routes style
  function getTrackLineStyle(feature: FeatureLike): Style | undefined{
    const trackId = feature.get('trackId');
    const selected = trackId === selectedTrackId;

    return new Style({
      stroke: new Stroke({
        color: selected ? "#1565c0" : "#888",
        width: 5
      })
    });
  }

  function rebuildTrackPoints(): void {
    const source = trackLayer?.getSource();
    if (!source) return;

    source.clear();

    for (const track of $trackItems) {
      const startFeature = new Feature({
        geometry: new Point(fromLonLat(track.startPoint)),
        trackId: track.id
      });

      source.addFeature(startFeature);
    }
  }

  function rebuildTrackLines(): void {
    const source = trackLineLayer?.getSource();
    if (!source) return;

    source.clear();

    const selectedTrack =
      $trackItems.find(track => track.id === selectedTrackId);

    if (!selectedTrack) return;

    const projectedCoords = selectedTrack.coordinates.map(
      ([lon, lat]) => fromLonLat([lon, lat])
    );

    source.addFeature(
      new Feature({
        geometry: new LineString(projectedCoords),
        trackId: selectedTrack.id
      })
    );
  }

  $: if (trackLayer && trackLineLayer) {
    $trackItems;

    rebuildTrackPoints();
    rebuildTrackLines();
  }

  $: if (trackLayer) {
    selectedTrackId;
    trackLayer.changed();
  }

  $: if (trackLineLayer) {
    $trackItems;
    selectedTrackId;
    rebuildTrackLines();
  }

  function selectTrack(track: TrackListItem): void {
    selectedTrackId = track.id;
    if (!map) return;

    const coords = track.coordinates.map(
      ([lon, lat]) => fromLonLat([lon, lat])
    );

    const extent = boundingExtent(coords);

    map.getView().fit(extent, {
      padding: [50, 50, 50, 50],
      duration: 500,
      maxZoom: 15
    });
  }

  let pendingDeleteTrack: TrackListItem | null = null;

  function promptDelete(track: TrackListItem): void {
    pendingDeleteTrack = track;
  }

  function toggleExport(trackId: number): void {
    toggleTrackQueued(trackId);
  }

  async function confirmDelete(): Promise<void> {
    if (!pendingDeleteTrack) return;

    const deletingTrack = pendingDeleteTrack;
    isDeleting = true;
    pageError = null;

    try {
      if (!$trackLoadState.usingDemoData) {
        await deleteTrack(deletingTrack.id);
      }
      removeTrackFromStores(deletingTrack.id);
      if (selectedTrackId === deletingTrack.id) {
        selectedTrackId = null;
      }
      pendingDeleteTrack = null;
    } catch (error: unknown) {
      console.error(`Failed to delete track ${deletingTrack.id}:`, error);
      pageError = error instanceof Error ? error.message : 'Failed to delete track.';
    } finally {
      isDeleting = false;
    }
  }

  function cancelDelete(): void {
    pendingDeleteTrack = null;
  }

  function goToManageData(): void {
    push('/ManageData');
  }

  onMount(() => {
    trackLayer = new VectorLayer({
      source: new VectorSource(),
      style: (feature) => getPointStyle(feature)
    });

    trackLineLayer = new VectorLayer({
      source: new VectorSource(),
      style: (feature) =>  getTrackLineStyle(feature)
    });

    map = new Map({
      target: mapElement,
      layers: [
        new TileLayer({ source: new OSM() }),
        trackLineLayer,
        trackLayer
      ],
      view: new View({
        center: fromLonLat([0, 0]),
        zoom: 2
      }),
      controls: defaultControls({ rotate: false })
    });

    void loadTracksFromApi();

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

      const clickedTrack = $trackItems.find((t) => t.id === trackId);
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
  <button class="appbar-shortcut-btn" type="button" onclick={goToManageData}>Data Manager</button>

  <div class="content-area">
    <!-- Map (left 75%) -->
    <div class="map-container">
      <div bind:this={mapElement} class="map"></div>
    </div>

    <!-- Right panel: search + track list (right 25%) -->
    <div class="right-panel">
      <div class="search-bar-container">
        <p class="panel-note">{$exportTrackCount} track{$exportTrackCount === 1 ? '' : 's'} queued for export.</p>
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
              type="button"
              onclick={() => selectTrack(track)}
            >
              <span class="track-name">{track.name}</span>
              <span class="track-meta">{track.date}</span>
              <span class="track-meta">{track.distanceMi.toFixed(1)} mi &bull; {formatDuration(track.durationMin)}</span>
            </button>
            <div class="track-actions">
              <button
                class="track-export-btn"
                class:track-export-btn--active={$exportTrackIds.includes(track.id)}
                type="button"
                title={$exportTrackIds.includes(track.id) ? 'Remove from export file' : 'Add to export file'}
                aria-label={$exportTrackIds.includes(track.id) ? 'Remove from export file' : 'Add to export file'}
                onclick={() => toggleExport(track.id)}
              >
                <img
                  src={$exportTrackIds.includes(track.id) ? export_remove_icon : export_add_icon}
                  alt={$exportTrackIds.includes(track.id) ? 'Remove from export file' : 'Add to export file'}
                />
              </button>
              <!-- svelte-ignore a11y_consider_explicit_label -->
              <button
                class="track-delete-btn"
                type="button"
                title="Delete track"
                onclick={() => promptDelete(track)}
              >
                <img src={trashcan_icon} alt="Trashcan" />
              </button>
            </div>
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
  <div class="modal-backdrop" onclick={cancelDelete}>
    <div class="modal" onclick={(event) => event.stopPropagation()}>
      <p class="modal-title">Are you sure you want to delete <strong>{pendingDeleteTrack.name}</strong>? This cannot be undone.</p>
      <div class="modal-actions">
        <button class="modal-btn modal-btn--cancel" type="button" onclick={cancelDelete}>Cancel</button>
        <button class="modal-btn modal-btn--confirm" type="button" disabled={isDeleting} onclick={confirmDelete}>
          {isDeleting ? 'Deleting...' : 'Delete'}
        </button>
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
    position: relative;
  }

  .appbar-shortcut-btn {
    position: absolute;
    top: 0.85rem;
    right: 1rem;
    z-index: 30;
    border: 1px solid #ffffff;
    border-radius: 6px;
    background-color: var(--secondary-color, rgb(225, 225, 225));
    color: #222222;
    padding: 0.45rem 0.7rem;
    font: inherit;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s ease, box-shadow 0.2s ease;
  }

  .appbar-shortcut-btn:hover {
    background-color: #f1f1f1;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
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

  .panel-note {
    margin: 0 0 0.55rem;
    font-size: 0.78rem;
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
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1 1 50%;
    width: 100%;
    min-height: 0;
    border: none;
    border-top: 1px solid #c0c0c0;
    background: transparent;
    color: #888;
    font-size: 0.85rem;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
  }

  .track-export-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1 1 50%;
    min-height: 0;
    border: none;
    border-bottom: 1px solid #c0c0c0;
    background: transparent;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .track-export-btn:hover {
    background: #d7f4e0;
  }

  .track-export-btn--active {
    background: #92e3a5;
  }

  .track-export-btn img {
    width: 22px;
    height: 22px;
    display: block;
  }

  .track-actions {
    display: flex;
    flex-direction: column;
    flex: 0 0 7.1rem;
    min-height: 0;
    border-left: 1px solid #c0c0c0;
  }

  .track-delete-btn:hover {
    background: #e57373;
    color: #fff;
  }

  .track-delete-btn img {
    width: 22px;
    height: 22px;
    display: block;
  }

  @media (max-width: 900px) {
    .right-panel {
      width: 38%;
    }
  }

  @media (max-width: 720px) {
    .appbar-shortcut-btn {
      top: 0.92rem;
      right: 0.6rem;
      padding: 0.4rem 0.6rem;
      font-size: 0.82rem;
    }

    .content-area {
      flex-direction: column;
    }

    .right-panel {
      width: 100%;
      min-width: 0;
      max-height: 45%;
      border-left: none;
      border-top: 2px solid #000000;
    }
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