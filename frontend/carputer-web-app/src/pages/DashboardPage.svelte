<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import BackButton from "../assets/components/BackButton.svelte";
  import SystemIndicators from "../assets/components/SystemIndicators.svelte";
  import check_mark from "../assets/check-circle-bold.svg";
  import download_icon from  "../assets/download-bold.svg";

  import OLMap from 'ol/Map.js';
  import View from 'ol/View.js';
  import TileLayer from 'ol/layer/Tile.js';
  import OSM from 'ol/source/OSM.js';
  import VectorLayer from 'ol/layer/Vector.js';
  import VectorSource from 'ol/source/Vector.js';
  import Feature from 'ol/Feature.js';
  import { fromExtent } from 'ol/geom/Polygon.js';
  import { Style, Fill, Stroke, Text } from 'ol/style.js';
  import { fromLonLat } from 'ol/proj.js';
  import { createXYZ } from 'ol/tilegrid.js';
  import 'ol/ol.css';

  // TODO: These values should be fetched from the backend, currently they are just placeholders for display.
  let num_tracks: number = 0;
  let patch_level: string = "0.1.2";

  // map state
  let mapElement: HTMLDivElement | undefined;
  let map: OLMap | undefined;
  let gridSource: VectorSource | undefined;
  let selectionSource: VectorSource | undefined;
  const tileGrid = createXYZ({ maxZoom: 22 });

  // tile selection state
  let isSelectMode: boolean = false;
  let hasSelection: boolean = false;
  // key: "z/x/y", value: [z, x, y] in OL internal coords
  let selectedTiles = new Map<string, [number, number, number]>();
  // download zoom level (controls tile grid cell size; lower = bigger tiles)
  let downloadZoom: number = 14;

  const gridStyle = new Style({
    fill: new Fill({ color: 'rgba(255, 255, 255, 0.04)' }),
    stroke: new Stroke({ color: 'rgba(255, 255, 255, 0.55)', width: 1 }),
  });

  const selectedTileStyle = new Style({
    fill: new Fill({ color: 'rgba(0, 120, 255, 0.25)' }),
    stroke: new Stroke({ color: 'rgba(0, 120, 255, 0.9)', width: 2 }),
    text: new Text({
      text: '✓',
      font: 'bold 28px sans-serif',
      fill: new Fill({ color: 'white' }),
      stroke: new Stroke({ color: 'rgba(0, 0, 0, 0.5)', width: 3 }),
    }),
  });

  function updateGrid(): void {
    if (!map || !gridSource) return;
    gridSource.clear();
    if (!isSelectMode) return;

    const size = map.getSize();
    if (!size) return;
    const extent = map.getView().calculateExtent(size);
    const z = downloadZoom;

    const minTc = tileGrid.getTileCoordForCoordAndZ([extent[0] as number, extent[1] as number], z);
    const maxTc = tileGrid.getTileCoordForCoordAndZ([extent[2] as number, extent[3] as number], z);
    const xMin = Math.min(minTc[1] as number, maxTc[1] as number);
    const xMax = Math.max(minTc[1] as number, maxTc[1] as number);
    const yMin = Math.min(minTc[2] as number, maxTc[2] as number);
    const yMax = Math.max(minTc[2] as number, maxTc[2] as number);

    // guard against accidental huge extents at low zoom levels
    if ((xMax - xMin + 1) * (yMax - yMin + 1) > 1000) return;

    for (let x = xMin; x <= xMax; x++) {
      for (let y = yMin; y <= yMax; y++) {
        const tileExtent = tileGrid.getTileCoordExtent([z, x, y]);
        const feature = new Feature(fromExtent(tileExtent));
        feature.setId(`grid/${z}/${x}/${y}`);
        gridSource.addFeature(feature);
      }
    }
  }

  // re-render grid whenever downloadZoom or isSelectMode changes
  $: if (map && gridSource) updateGrid();

  onMount(() => {
    gridSource = new VectorSource();
    selectionSource = new VectorSource();

    const gridLayer = new VectorLayer({ source: gridSource, style: gridStyle });
    const selectionLayer = new VectorLayer({
      source: selectionSource,
      style: selectedTileStyle,
    });

    map = new OLMap({
      target: mapElement,
      layers: [
        new TileLayer({ source: new OSM() }),
        gridLayer,
        selectionLayer,
      ],
      view: new View({
        center: fromLonLat([0, 0]),
        zoom: 3,
      }),
      controls: [],
    });

    map.on('moveend', updateGrid);

    // center on the user's current location if available
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          map?.getView().animate({
            center: fromLonLat([pos.coords.longitude, pos.coords.latitude]),
            zoom: 12,
            duration: 600,
          });
        },
        () => { /* geolocation denied – stay at default world view */ }
      );
    }

    map.on('click', (event) => {
      if (!isSelectMode || !map || !selectionSource) return;

      const coord = event.coordinate;
      const zoom = Math.floor(map.getView().getZoom() ?? 10);
      const tc = tileGrid.getTileCoordForCoordAndZ(coord, zoom);
      const key = `${tc[0]}/${tc[1]}/${tc[2]}`;

      if (selectedTiles.has(key)) {
        selectedTiles.delete(key);
        const existing = selectionSource.getFeatureById(key);
        if (existing) selectionSource.removeFeature(existing);
      } else {
        selectedTiles.set(key, [tc[0] as number, tc[1] as number, tc[2] as number]);
        const extent = tileGrid.getTileCoordExtent(tc);
        const feature = new Feature(fromExtent(extent));
        feature.setId(key);
        selectionSource.addFeature(feature);
      }

      hasSelection = selectedTiles.size > 0;
      // reassign to trigger Svelte reactivity
      selectedTiles = new Map(selectedTiles);
    });
  });

  onDestroy(() => {
    map?.setTarget(undefined);
  });

  function toggleSelectMode(): void {
    isSelectMode = !isSelectMode;
    // updateGrid() is called reactively via $: when isSelectMode changes
  }

  function clearSelection(): void {
    selectionSource?.clear();
    selectedTiles = new Map();
    hasSelection = false;
  }

  async function downloadTiles(): Promise<void> {
    if (!hasSelection) return;
    const tiles = [...selectedTiles.values()].map(([z, x, y]) => ({ z, x, y }));
    // TODO: hook up to real backend endpoint
    console.log('Download tiles request:', { tiles, downloadZoom });
    // await fetch('/api/tiles/download', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ tiles, zoom: downloadZoom }),
    // });
  }
</script>


<div class="translucent-overlay" style="overflow-y: hidden;">

  <!-- this is a box to show the title -->
  <div class="title-box"> 
      <!-- this is the exit button -->
    <BackButton />
    <h2>System Info</h2>

    <SystemIndicators 
      isActiveBackground={false} 
      isRoadDiscoverActive={false}
    />
  </div>

 <div class="body-container">

  <div class="left-column">

  <!-- this contains both the information of the system and import/export button-->
  <div class="seperate-vert">

    <!-- this is the information of the system -->
    <div class="seperate-hori">
      <div class="info-box">
        <p class="info-row">
          <span class="info-label">Number of GPS Tracks:</span>
          <span class="info-value">{num_tracks}</span>
        </p>
      </div>
      
      <div class="info-box">
        <p class="info-row">
          <span class="info-label">Current Patch Level:</span>
          <span class="info-value">{patch_level}</span>
        </p>
      </div>
    </div>
  </div>

  <div class="update-box">
    <!-- this button is for checking updates of the system.-->
    <button class="button-color">
      <img src={check_mark} alt="Check" class="icons" />
      Check for Updates
    </button>
  </div>

  </div>

  <div class="download-box">
    <!-- map controls bar -->
    <div class="map-controls">
      <button
        class="map-ctrl-btn"
        class:map-ctrl-btn--active={isSelectMode}
        on:click={toggleSelectMode}
      >
        {isSelectMode ? 'Stop Selecting' : 'Select Tiles'}
      </button>

      <button
        class="map-ctrl-btn"
        disabled={!hasSelection}
        on:click={clearSelection}
      >
        Clear
      </button>

      <label class="zoom-label">
        Tile Size
        <span class="zoom-coarse">Coarse</span>
        <input class="zoom-slider" type="range" min="6" max="18" step="1" bind:value={downloadZoom} />
        <span class="zoom-fine">Fine</span>
        <span class="zoom-value">z{downloadZoom}</span>
      </label>

      <button
        class="map-ctrl-btn map-ctrl-btn--download"
        disabled={!hasSelection}
        on:click={downloadTiles}
      >
        <img src={download_icon} alt="Download" class="icons" />
        Download Map
      </button>
    </div>

    <!-- map fills the remaining space -->
    <div class="map-container" class:select-mode={isSelectMode} bind:this={mapElement}></div>
  </div>

 </div>
  
</div>

<style>
  .translucent-overlay {
    display: flex;
    flex-direction: column;
    height: 100%;
    box-sizing: border-box;
  }

  .body-container {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    flex: 1;
    min-height: 0;
    gap: 12px;
    padding: 8px;
    box-sizing: border-box;
    width: 100%;
    overflow-y: hidden;
  }

  .left-column {
    width: 40%;
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }


  .info-box {
    display: flex;
    align-items: center;
    min-height: 0;
    color: black;
    margin: 0;
  }

  .seperate-vert {
    display: flex;
    justify-content: space-between;
    position: relative;
    padding-left: 2%;
    padding-right: 2%;
    box-sizing: border-box;
    align-items: center;
    background-color: var(--secondary-color);
    width: 100%;
    flex: 1;
    border-width: 2px;
    border-color: rgb(255, 255, 255);
    border-style: solid;
  }

  .seperate-hori {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    gap: 8px;
    height: 100%;
    width: 100%;
    padding-top: 8px;
    padding-bottom: 8px;
    box-sizing: border-box;
  }

  .info-row {
    display: grid;
    grid-template-columns: minmax(140px, auto) auto;
    align-items: center;
    column-gap: 8px;
    margin: 0;
    width: 100%;
  }

  .info-label {
    white-space: nowrap;
  }

  .info-value {
    font-weight: 600;
  }

  .update-box {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    position: relative;
    background-color: var(--secondary-color);
    width: 100%;
    flex: 1;
    box-sizing: border-box;
    padding-left: 5%;
    border-width: 2px;
    border-color: rgb(255, 255, 255);
    border-style: solid;
  }

  .download-box {
    display: flex;
    flex-direction: column;
    position: relative;
    box-sizing: border-box;
    background-color: var(--secondary-color);
    width: 60%;
    height: 100%;
    min-height: 0;
    border-width: 2px;
    border-color: rgb(255, 255, 255);
    border-style: solid;
    overflow: hidden;
  }

  .map-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background-color: var(--secondary-color);
    border-bottom: 1px solid rgba(255, 255, 255, 0.3);
    flex-shrink: 0;
    flex-wrap: wrap;
  }

  .map-container {
    flex: 1;
    min-height: 0;
    width: 100%;
  }

  /* force OL canvas to fill the container */
  .map-container :global(.ol-viewport) {
    width: 100% !important;
    height: 100% !important;
  }

  /* crosshair cursor while in tile-select mode */
  .map-container.select-mode :global(.ol-viewport),
  .map-container.select-mode :global(canvas) {
    cursor: crosshair !important;
  }

  .map-ctrl-btn {
    background-color: rgba(188, 188, 188, 1);
    color: black;
    border: none;
    outline: none;
    padding: 4px 10px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
  }
  .map-ctrl-btn:hover:not(:disabled) {
    background-color: rgba(210, 210, 210, 1);
  }
  .map-ctrl-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  .map-ctrl-btn--active {
    background-color: rgba(0, 120, 255, 0.85);
    color: white;
  }
  .map-ctrl-btn--active:hover {
    background-color: rgba(0, 100, 230, 0.9);
  }
  .map-ctrl-btn--download {
    margin-left: auto;
  }

  .zoom-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    color: black;
    white-space: nowrap;
  }

  .zoom-coarse,
  .zoom-fine {
    font-size: 0.75rem;
    opacity: 0.7;
  }

  .zoom-slider {
    width: 120px;
    cursor: pointer;
    accent-color: rgba(0, 120, 255, 0.85);
  }

  .zoom-value {
    font-size: 0.8rem;
    font-weight: 600;
    min-width: 28px;
    text-align: left;
  }

  .button-color {
    background-color: rgba(188, 188, 188);

    color: black;

    outline: none;

    display: flex;
    align-items: center;

    justify-content: center;
    border: none;
  }
  .button-color:hover {
    background-color: rgba(202, 202, 202);
  }

  .icons {
    width: 24px;
    height: 24px;
    margin-right: 8px;
  }

</style>
