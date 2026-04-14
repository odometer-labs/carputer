<script lang="ts">
  import { onMount } from 'svelte';
  import Map from 'ol/Map.js';
  import View from 'ol/View.js';
  import TileLayer from 'ol/layer/Tile.js';
  import OSM from 'ol/source/OSM.js';
  import { defaults as defaultControls } from 'ol/control/defaults.js';
  import { fromLonLat } from 'ol/proj.js';
  import 'ol/ol.css';
  import AppBar from '../assets/components/AppBar.svelte';

  // --- Types (matches expected backend shape) ---
  interface Track {
    id: number;
    name: string;
    date: string;        // ISO date string
    distanceMi: number;
    durationMin: number;
  }

  // --- Fake data: swap this out for an API fetch when backend is ready ---
  const FAKE_TRACKS: Track[] = [
    { id: 1, name: 'Morning Commute',  date: '2026-04-13', distanceMi: 8.2,   durationMin: 22  },
    { id: 2, name: 'Weekend Drive',    date: '2026-04-12', distanceMi: 45.1,  durationMin: 74  },
    { id: 3, name: 'Grocery Run',      date: '2026-04-11', distanceMi: 3.4,   durationMin: 11  },
    { id: 4, name: 'Highway Test',     date: '2026-04-10', distanceMi: 120.6, durationMin: 95  },
    { id: 5, name: 'City Loop',        date: '2026-04-09', distanceMi: 15.8,  durationMin: 38  },
    { id: 6, name: 'Mountain Road',    date: '2026-04-08', distanceMi: 62.3,  durationMin: 110 },
    { id: 7, name: 'Night Drive',      date: '2026-04-07', distanceMi: 28.9,  durationMin: 45  },
  ];

  let mapElement: HTMLDivElement | undefined;
  let map: Map | undefined;
  let searchQuery: string = '';
  let selectedTrackId: number | null = null;

  // Mutable working copy — replace with reactive store / API state when backend is ready
  let tracks: Track[] = [...FAKE_TRACKS];

  $: filteredTracks = tracks.filter(t =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.date.includes(searchQuery)
  );

  function formatDuration(minutes: number): string {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }

  function selectTrack(track: Track): void {
    selectedTrackId = track.id;
    // TODO: fetch track geometry from backend and render on map
  }

  let pendingDeleteTrack: Track | null = null;

  function promptDelete(track: Track): void {
    pendingDeleteTrack = track;
  }

  function confirmDelete(): void {
    if (!pendingDeleteTrack) return;
    // TODO: call DELETE /api/tracks/:id before updating local state
    if (selectedTrackId === pendingDeleteTrack.id) selectedTrackId = null;
    tracks = tracks.filter(t => t.id !== pendingDeleteTrack!.id);
    pendingDeleteTrack = null;
  }

  function cancelDelete(): void {
    pendingDeleteTrack = null;
  }

  onMount(() => {
    map = new Map({
      target: mapElement,
      layers: [
        new TileLayer({ source: new OSM() })
      ],
      view: new View({
        center: fromLonLat([0, 0]),
        zoom: 2
      }),
      controls: defaultControls({ rotate: false })
    });

    return () => {
      map?.setTarget(undefined);
    };
  });
</script>

<main class="tracks-shell">
  <AppBar />

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
              &#x2715;
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