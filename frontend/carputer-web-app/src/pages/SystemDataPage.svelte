<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import BackButton from "../assets/components/BackButton.svelte";
  import SystemIndicators from "../assets/components/SystemIndicators.svelte";
  import check_mark from "../assets/icons/check-circle-bold.svg";
  import download_icon from  "../assets/icons/download-bold.svg";
  import update_icon from "../assets/icons/refresh-circle.svg";
  import OLMap from 'ol/Map.js';
  import View from 'ol/View.js';
  import TileLayer from 'ol/layer/Tile.js';
  import OSM from 'ol/source/OSM.js';
  import VectorLayer from 'ol/layer/Vector.js';
  import VectorSource from 'ol/source/Vector.js';
  import Feature from 'ol/Feature.js';
  import Point from 'ol/geom/Point.js';
  import Polygon, { fromExtent } from 'ol/geom/Polygon.js';
  import { containsExtent, getIntersection } from 'ol/extent.js';
  import { Style, Fill, Stroke, Text, Circle } from 'ol/style.js';
  import { fromLonLat } from 'ol/proj.js';
  import { createXYZ } from 'ol/tilegrid.js';
  import { 
    createRegion, 
    deleteRegion,
    listRegions,
    listTracks,
    getCurrentPosition, 
    getLatestVersion, 
    subscribeToPositionStream, 
    subscribeToSysHealth 
  } from '../api/restApi';
  import type { GPSData, RegionDataModel, SysHealthData } from '../api/types';
  import { reportNonVitalError } from '../stores/errorStore';
  import { wifiStore } from '../stores/wifiStore';
  import 'ol/ol.css';
  import { trackStore } from '../stores/trackStore';
  import { wifiStore } from '../stores/wifiStore';

  // TODO: These values should be fetched from the backend, currently they are just placeholders for display.
  let storage_amount_dowloaded: string = "Unknown";

  //to hold the speed value from GPSData
  let speed_mph: number = 0;

  // to hold the patch level
  let versionNumber = "Loading...";
  let gitHash = "Loading...";
  let releaseDate = "Loading...";

  //incase the version didn't get loaded then it would let the user know.
  let versionLoadFailed = false;

  let sysHealth: SysHealthData | null = null;
  let stopSysHealthSubscription: (() => void) | null = null;

  function formatBytes(bytes: number): string {
    if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)}G`;
    if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(0)}M`;
    if (bytes >= 1_024) return `${(bytes / 1_024).toFixed(0)}K`;
    return `${bytes}B`;
  }

  function formatUptime(seconds: number): string {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (d > 0) return `${d}d ${h}h`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  }

  // update checking state
  type UpdateState = 'idle' | 'checking' | 'no-updates' | 'updates-available' | 'updating' | 'updated';
  let updateCheckState: UpdateState = 'idle';

  // map state
  let mapElement: HTMLDivElement | undefined;
  let map: OLMap | undefined;
  let gridLayer: VectorLayer | undefined;
  let gridSource: VectorSource | undefined;
  let selectionSource: VectorSource | undefined;
  let userLayer: VectorLayer | undefined;
  let userMarker: Feature<Point> | undefined;
  let userSource: VectorSource | undefined;
  let gridRenderRaf: number | null = null;
  let stopGPSSubscription: (() => void) | null = null;
  const GRID_ZOOM_OFFSET = 1;
  const tileGrid = createXYZ({ maxZoom: 22 });

  const OREGON_SW = fromLonLat([-124.848974, 41.991794]) as [number, number];
  const OREGON_NE = fromLonLat([-116.463504, 46.292035]) as [number, number];
  const OREGON_CENTER = fromLonLat([-120.6565, 44.1428]) as [number, number];
  const OREGON_EXTENT: [number, number, number, number] = [
    OREGON_SW[0],
    OREGON_SW[1],
    OREGON_NE[0],
    OREGON_NE[1],
  ];

  const OREGON_POLYGON = new Polygon([[
    [-123.994551,45.944106],
    [-124.01, 46.10], // Warrenton
    [-124.00, 46.18], // Clatsop Spit
    [-123.95, 46.25], // Mouth of Columbia
    [-123.83, 46.22], // Astoria North
    [-123.75, 46.23], // Tongue Point
    [-123.545441,46.261769],
    [-123.370179,46.146753],
    [-123.211348,46.174138],
    [-123.11824,46.185092],
    [-122.904639,46.08103],
    [-122.811531,45.960537],
    [-122.762239,45.659305],
    [-122.247407,45.549767],
    [-121.809251,45.708598],
    [-121.535404,45.725029],
    [-121.217742,45.670259],
    [-121.18488,45.604536],
    [-120.637186,45.746937],
    [-120.505739,45.697644],
    [-120.209985,45.725029],
    [-119.963522,45.823614],
    [-119.525367,45.911245],
    [-119.125551,45.933153],
    [-118.988627,45.998876],
    [-116.918344,45.993399],
    [-116.78142,45.823614],
    [-116.545912,45.752413],
    [-116.463758,45.61549],
    [-116.671881,45.319735],
    [-116.732128,45.144473],
    [-116.847143,45.02398],
    [-116.830713,44.930872],
    [-116.934774,44.782995],
    [-117.038836,44.750133],
    [-117.241483,44.394132],
    [-117.170283,44.257209],
    [-116.97859,44.240778],
    [-116.896436,44.158624],
    [-117.027882,43.830007],
    [-117.027882,42.000709],
    [-118.698349,41.989755],
    [-120.001861,41.995232],
    [-121.037003,41.995232],
    [-122.378853,42.011663],
    [-123.233256,42.006186],
    [-124.213628,42.000709],
    [-124.356029,42.115725],
    [-124.432706,42.438865],
    [-124.416275,42.663419],
    [-124.553198,42.838681],
    [-124.454613,43.002989],
    [-124.383413,43.271359],
    [-124.235536,43.55616],
    [-124.169813,43.8081],
    [-124.060274,44.657025],
    [-124.076705,44.772041],
    [-123.97812,45.144473],
    [-123.939781,45.659305],
    [-123.994551,45.944106]
  ].map(coord => fromLonLat(coord))]);

  // tile selection state
  let isSelectMode: boolean = false;
  let hasSelection: boolean = false;
  let hasPendingTileSyncChanges: boolean = false;
  let isSyncingTileSelection: boolean = false;
  let canDownloadTiles: boolean = false;
  // key: "z/x/y", value: [z, x, y] in OL internal coords
  let selectedTiles = new Map<string, [number, number, number]>();
  // key: "z/x/y", value: region id in backend
  let downloadedRegionIdsByTileKey = new Map<string, number>();

  //get the storage amount left
  $: storageRemaining = sysHealth
    ? formatBytes(sysHealth.disk.total_bytes - sysHealth.disk.used_bytes)
    : "Loading...";

  type DownloadedTile = {
    id: number;
    z: number;
    x: number;
    y: number;
  };

  const TILE_REGION_PREFIX = 'tile/';

  const userMarkerStyle = new Style({
    image: new Circle({
      radius: 10,
      fill: new Fill({ color: '#3399CC' }),
      stroke: new Stroke({ color: '#ffffff', width: 2 }),
    }),
  });

  const gridStyle = new Style({
    fill: new Fill({ color: 'rgba(255, 255, 255, 0.04)' }),
    stroke: new Stroke({ color: 'rgba(0, 0, 0, 0.75)', width: 1 }),
  });

  const selectedTileStyle = new Style({
    fill: new Fill({ color: 'rgba(0, 120, 255, 0.25)' }),
    stroke: new Stroke({ color: 'rgba(0, 120, 255, 0.9)', width: 2 }),
    text: new Text({
      font: 'bold 28px sans-serif',
      fill: new Fill({ color: 'white' }),
      stroke: new Stroke({ color: 'rgba(0, 0, 0, 0.5)', width: 3 }),
    }),
  });

  function updateUserMarker(coords: [number, number]): void {
    if (!map) return;

    if (!userMarker) {
      userMarker = new Feature({
        geometry: new Point(coords),
      });
      userMarker.setStyle(userMarkerStyle);

      userSource = new VectorSource({
        features: [userMarker],
      });

      userLayer = new VectorLayer({
        source: userSource,
        updateWhileAnimating: true,
        updateWhileInteracting: true,
      });

      map.addLayer(userLayer);
    } else {
      const geometry = userMarker.getGeometry();
      if (geometry) {
        geometry.setCoordinates(coords);
      } else {
        userMarker.setGeometry(new Point(coords));
      }
      userSource?.changed();
    }

  }

  function handleGPSPosition(position: GPSData): void {
    const lon = Number(position.longitude);
    const lat = Number(position.latitude);

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      return;
    }

    const coords = fromLonLat([lon, lat]) as [number, number];
    updateUserMarker(coords);

    //update the speed_mph to show on the dashboard
    speed_mph = position.speed;
  }

  function updateGrid(): void {
    if (!map || !gridSource) return;
    if (!isSelectMode) return;

    const size = map.getSize();
    if (!size) return;
    const extent = map.getView().calculateExtent(size);
    const viewZoom = Math.floor(map.getView().getZoom() ?? 10);
    const z = Math.max(0, Math.min(22, viewZoom + GRID_ZOOM_OFFSET));

    const minTc = tileGrid.getTileCoordForCoordAndZ([extent[0] as number, extent[1] as number], z);
    const maxTc = tileGrid.getTileCoordForCoordAndZ([extent[2] as number, extent[3] as number], z);
    const viewportXMin = Math.min(minTc[1] as number, maxTc[1] as number);
    const viewportXMax = Math.max(minTc[1] as number, maxTc[1] as number);
    const viewportYMin = Math.min(minTc[2] as number, maxTc[2] as number);
    const viewportYMax = Math.max(minTc[2] as number, maxTc[2] as number);

    const oregonMinTc = tileGrid.getTileCoordForCoordAndZ([OREGON_EXTENT[0], OREGON_EXTENT[1]], z);
    const oregonMaxTc = tileGrid.getTileCoordForCoordAndZ([OREGON_EXTENT[2], OREGON_EXTENT[3]], z);

    const oregonXMin = Math.min(oregonMinTc[1] as number, oregonMaxTc[1] as number);
    const oregonXMax = Math.max(oregonMinTc[1] as number, oregonMaxTc[1] as number);
    const oregonYMin = Math.min(oregonMinTc[2] as number, oregonMaxTc[2] as number);
    const oregonYMax = Math.max(oregonMinTc[2] as number, oregonMaxTc[2] as number);

    const xMin = Math.max(viewportXMin, oregonXMin);
    const xMax = Math.min(viewportXMax, oregonXMax);
    const yMin = Math.max(viewportYMin, oregonYMin);
    const yMax = Math.min(viewportYMax, oregonYMax);

    if (xMin > xMax || yMin > yMax) {
      gridSource.clear();
      return;
    }

    // Guard against accidental huge extents at low map zoom levels.
    // If too many cells would be rendered, keep the existing grid visible instead of clearing it.
    const cellCount = (xMax - xMin + 1) * (yMax - yMin + 1);
    if (cellCount > 25000) return;

    gridSource.clear();

    for (let x = xMin; x <= xMax; x++) {
      for (let y = yMin; y <= yMax; y++) {
        const tileCoord: [number, number, number] = [z, x, y];
        const tileExtent = tileGrid.getTileCoordExtent(tileCoord);
        if (!OREGON_POLYGON.intersectsExtent(tileExtent)) {
          continue;
        }

        const feature = new Feature(fromExtent(tileExtent));
        feature.setId(`grid/${z}/${x}/${y}`);
        gridSource.addFeature(feature);
      }
    }
  }

  function isTileInsideOregon(tileCoord: [number, number, number]): boolean {
    const tileExtent = tileGrid.getTileCoordExtent(tileCoord);
    return OREGON_POLYGON.intersectsExtent(tileExtent);
  }

  function scheduleGridUpdate(): void {
    if (gridRenderRaf !== null) return;

    gridRenderRaf = requestAnimationFrame(() => {
      gridRenderRaf = null;
      updateGrid();
    });
  }

  // re-render grid whenever select mode changes
  $: if (map && gridSource) updateGrid();
  $: hasPendingTileSyncChanges = selectionDiffersFromDownloaded();
  $: canDownloadTiles = $wifiStore.isWifiOn && $wifiStore.isConnected;


  function regionNameFromTileKey(tileKey: string): string {
    return `${TILE_REGION_PREFIX}${tileKey}`;
  }

  function tileKeyFromRegionName(regionName: string): string | null {
    if (typeof regionName !== 'string' || !regionName.startsWith(TILE_REGION_PREFIX)) {
      return null;
    }

    const tileKey = regionName.slice(TILE_REGION_PREFIX.length);
    const segments = tileKey.split('/');
    if (segments.length !== 3) return null;

    if (!segments.every((segment) => /^-?\d+$/.test(segment))) {
      return null;
    }

    return tileKey;
  }

  function tileCoordFromKey(tileKey: string): [number, number, number] | null {
    const segments = tileKey.split('/');
    if (segments.length !== 3) return null;

    const z = Number(segments[0]);
    const x = Number(segments[1]);
    const y = Number(segments[2]);

    if (!Number.isFinite(z) || !Number.isFinite(x) || !Number.isFinite(y)) {
      return null;
    }

    return [Math.floor(z), Math.floor(x), Math.floor(y)];
  }

  function selectionDiffersFromDownloaded(): boolean {
    if (selectedTiles.size !== downloadedRegionIdsByTileKey.size) {
      return true;
    }

    for (const key of selectedTiles.keys()) {
      if (!downloadedRegionIdsByTileKey.has(key)) {
        return true;
      }
    }

    return false;
  }

  async function loadDownloadedRegions(): Promise<void> {
    try {
      const regions = await listRegions();
      applyDownloadedRegionSelections(regions);
    } catch (error: unknown) {
      reportNonVitalError(error, 'SystemDataPage.listRegions');
    }
  }

  function startGPSTracking(): void {
    getCurrentPosition()
      .then((position) => handleGPSPosition(position))
      .catch((error: unknown) => {
        reportNonVitalError(error, 'SystemDataPage.getCurrentPosition');
      });

    stopGPSSubscription = subscribeToPositionStream(
      (position: GPSData) => {
        handleGPSPosition(position);
      },
      (error: string) => {
        reportNonVitalError(error, 'SystemDataPage.subscribeToPositionStream');
      }
    );
  }

  async function handleCheckForUpdates(): Promise<void> {
    updateCheckState = 'checking';
    try {
      // TODO: Replace with actual backend API call to check for updates
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // TODO: Determine if updates are available from backend response
      const updatesAvailable = false;
      
      if (updatesAvailable) {
        updateCheckState = 'updates-available';
      } else {
        updateCheckState = 'no-updates';
      }
    } catch (error: unknown) {
      reportNonVitalError(error, 'SystemDataPage.handleCheckForUpdates');
      updateCheckState = 'idle';
    }
  }

  async function handleUpdate(): Promise<void> {
    updateCheckState = 'updating';
    try {
      // TODO: Replace with actual backend API call to initiate update
      await new Promise(resolve => setTimeout(resolve, 2500));
      updateCheckState = 'updated';
    } catch (error: unknown) {
      reportNonVitalError(error, 'SystemDataPage.handleUpdate');
      updateCheckState = 'updates-available';
    }
  }

  onMount(() => {
    //load patchlevel info
    loadPatchLevelInfo();

    gridSource = new VectorSource();
    selectionSource = new VectorSource();

    gridLayer = new VectorLayer({ source: gridSource, style: gridStyle });
    const selectionLayer = new VectorLayer({
      source: selectionSource,
      style: selectedTileStyle,
    });

    const clipFunction = (event: any) => {
      const ctx = event.context;
      const pixelRatio = event.frameState.pixelRatio;
      
      ctx.save();
      ctx.beginPath();
      
      const flatCoords = OREGON_POLYGON.getFlatCoordinates();
      const stride = OREGON_POLYGON.getStride();
      
      for (let i = 0; i < flatCoords.length; i += stride) {
        const coord = [flatCoords[i], flatCoords[i+1]] as [number, number];
        const pixel = map?.getPixelFromCoordinate(coord) as [number, number] | undefined;
        if (pixel) {
          if (i === 0) {
            ctx.moveTo(pixel[0] * pixelRatio, pixel[1] * pixelRatio);
          } else {
            ctx.lineTo(pixel[0] * pixelRatio, pixel[1] * pixelRatio);
          }
        }
      }
      
      ctx.closePath();
      ctx.clip();
    };

    const restoreFunction = (event: any) => {
      event.context.restore();
    };

    gridLayer.on('prerender', clipFunction);
    gridLayer.on('postrender', restoreFunction);
    selectionLayer.on('prerender', clipFunction);
    selectionLayer.on('postrender', restoreFunction);

    map = new OLMap({
      target: mapElement,
      layers: [
        new TileLayer({ source: new OSM() }),
        gridLayer,
        selectionLayer,
      ],
      view: new View({
        center: OREGON_CENTER,
        zoom: 7,
        extent: OREGON_EXTENT,
      }),
      controls: [],
    });

    // Keep grid responsive while dragging/zooming without running updateGrid too often.
    map.on('pointerdrag', scheduleGridUpdate);
    map.getView().on('change:center', scheduleGridUpdate);
    map.getView().on('change:resolution', scheduleGridUpdate);
    map.on('moveend', scheduleGridUpdate);

    startGPSTracking();

    stopSysHealthSubscription = subscribeToSysHealth(
      (data) => { sysHealth = data; },
      (error: string) => { sysHealth = null; reportNonVitalError(error, 'SystemDataPage.sysHealth'); }
    );

    loadDownloadedRegions();

    map.on('click', async (event: any) => {
      if (!isSelectMode || !map || !selectionSource || !gridLayer) return;

      const feature = map.forEachFeatureAtPixel(
        event.pixel,
        (candidate: any) => candidate,
        {
          layerFilter: (layer: any) => layer === gridLayer,
          hitTolerance: 3,
        }
      );

      if (!feature) return;
      const featureId = feature.getId();
      if (typeof featureId !== 'string' || !featureId.startsWith('grid/')) return;

      const parts = featureId.split('/');
      if (parts.length !== 4) return;

      const z = Number(parts[1]);
      const x = Number(parts[2]);
      const y = Number(parts[3]);
      if (!Number.isFinite(z) || !Number.isFinite(x) || !Number.isFinite(y)) return;

      const candidateTile: [number, number, number] = [z, x, y];
      if (!isTileInsideOregon(candidateTile)) return;

      // When zoomed out, big tiles should be split into smaller tiles that are actually in Oregon.
      const TARGET_SUBDIVISION_ZOOM = 10;
      const tilesToToggle = (z < TARGET_SUBDIVISION_ZOOM)
        ? getSubTiles(candidateTile, TARGET_SUBDIVISION_ZOOM).filter(t => isTileInsideOregon(t))
        : [candidateTile];

      // If any of the target tiles are already selected, we are in "deselect" mode for the whole set.
      const isDeselect = tilesToToggle.some(t => selectedTiles.has(`${t[0]}/${t[1]}/${t[2]}`));

      for (const t of tilesToToggle) {
        const key = `${t[0]}/${t[1]}/${t[2]}`;
        if (isDeselect) {
          if (selectedTiles.has(key)) {
            await toggleTile(t);
          }
        } else {
          if (!selectedTiles.has(key)) {
            await toggleTile(t);
          }
        }
      }

      hasSelection = selectedTiles.size > 0;
      // reassign to trigger Svelte reactivity
      selectedTiles = new Map(selectedTiles);
    });
  });

  onDestroy(() => {
    if (gridRenderRaf !== null) {
      cancelAnimationFrame(gridRenderRaf);
      gridRenderRaf = null;
    }
    stopGPSSubscription?.();
    stopGPSSubscription = null;
    stopSysHealthSubscription?.();
    stopSysHealthSubscription = null;
    map?.setTarget(undefined);
  });

  function toggleSelectMode(): void {
    isSelectMode = !isSelectMode;
    if (!isSelectMode) {
      gridSource?.clear();
    } else {
      scheduleGridUpdate();
    }
    // updateGrid() is called reactively via $: when isSelectMode changes
  }

  async function clearSelection(): Promise<void> {
    const tilesToClear = [...selectedTiles.values()];
    for (const tile of tilesToClear) {
      await toggleTile(tile);
    }

    hasSelection = selectedTiles.size > 0;
    selectedTiles = new Map(selectedTiles);
  }

  function getSubTiles(tile: [number, number, number], targetZ: number): [number, number, number][] {
    const [z, x, y] = tile;
    if (z >= targetZ) return [tile];

    const dz = targetZ - z;
    const factor = Math.pow(2, dz);
    const result: [number, number, number][] = [];
    const minX = x * factor;
    const maxX = (x + 1) * factor - 1;
    const minY = y * factor;
    const maxY = (y + 1) * factor - 1;

    // Safety check - don't return more than 4096 tiles from one click
    if ((maxX - minX + 1) * (maxY - minY + 1) > 4096) {
      return [tile];
    }

    for (let i = minX; i <= maxX; i++) {
      for (let j = minY; j <= maxY; j++) {
        result.push([targetZ, i, j]);
      }
    }
    return result;
  }

  async function toggleTile(tile: [number, number, number]): Promise<void> {
    if (!selectionSource) return;
    const [z, x, y] = tile;
    const key = `${z}/${x}/${y}`;

    if (selectedTiles.has(key)) {
      selectedTiles.delete(key);
      const existing = selectionSource.getFeatureById(key);
      if (existing) selectionSource.removeFeature(existing);

      const downloadedRegionId = downloadedRegionIdsByTileKey.get(key);
      if (downloadedRegionId !== undefined) {
        try {
          await deleteRegion(downloadedRegionId);
          downloadedRegionIdsByTileKey.delete(key);
          downloadedRegionIdsByTileKey = new Map(downloadedRegionIdsByTileKey);
        } catch (error: unknown) {
          reportNonVitalError(error, 'SystemDataPage.deleteRegionOnUnselect');

          // Roll back local deselection when backend delete fails.
          selectedTiles.set(key, tile);
          const rollbackExtent = tileGrid.getTileCoordExtent(tile);
          const rollbackFeature = new Feature(fromExtent(rollbackExtent));
          rollbackFeature.setId(key);
          selectionSource.addFeature(rollbackFeature);
        }
      }
    } else {
      const ancestorsToRemove: string[] = [];
      const descendantsToRemove: string[] = [];

      for (const [sKey, sTile] of selectedTiles.entries()) {
        if (sTile[0] < z && tileContains(sTile, tile)) {
          ancestorsToRemove.push(sKey);
        }
        if (sTile[0] > z && tileContains(tile, sTile)) {
          descendantsToRemove.push(sKey);
        }
      }

      for (const sKey of ancestorsToRemove) {
        selectedTiles.delete(sKey);
        const f = selectionSource.getFeatureById(sKey);
        if (f) selectionSource.removeFeature(f);
      }
      for (const sKey of descendantsToRemove) {
        selectedTiles.delete(sKey);
        const f = selectionSource.getFeatureById(sKey);
        if (f) selectionSource.removeFeature(f);
      }

      selectedTiles.set(key, tile);
      const extent = tileGrid.getTileCoordExtent(tile);
      const feature = new Feature(fromExtent(extent));
      feature.setId(key);
      selectionSource.addFeature(feature);
    }
  }

  function tileContains(
    outerTile: [number, number, number],
    innerTile: [number, number, number]
  ): boolean {
    const outerExtent = tileGrid.getTileCoordExtent(outerTile);
    const innerExtent = tileGrid.getTileCoordExtent(innerTile);
    return containsExtent(outerExtent, innerExtent);
  }

  function applyDownloadedTileSelections(downloadedTiles: DownloadedTile[]): void {
    if (!selectionSource) return;

    selectionSource.clear();
    selectedTiles = new Map();
    downloadedRegionIdsByTileKey = new Map();

    for (const tile of downloadedTiles) {
      if (!Number.isFinite(tile.id) || !Number.isFinite(tile.z) || !Number.isFinite(tile.x) || !Number.isFinite(tile.y)) {
        continue;
      }

      const z = Math.floor(tile.z);
      const x = Math.floor(tile.x);
      const y = Math.floor(tile.y);
      const key = `${z}/${x}/${y}`;
      const coord: [number, number, number] = [z, x, y];

      selectedTiles.set(key, coord);
      downloadedRegionIdsByTileKey.set(key, Math.floor(tile.id));

      const extent = tileGrid.getTileCoordExtent(coord);
      const feature = new Feature(fromExtent(extent));
      feature.setId(key);
      selectionSource.addFeature(feature);
    }

    hasSelection = selectedTiles.size > 0;
    selectedTiles = new Map(selectedTiles);
    downloadedRegionIdsByTileKey = new Map(downloadedRegionIdsByTileKey);
  }

  function applyDownloadedRegionSelections(regions: RegionDataModel[]): void {
    const downloadedTiles: DownloadedTile[] = [];

    for (const region of regions) {
      const tileKey = tileKeyFromRegionName(region.name);
      if (!tileKey) continue;

      const coord = tileCoordFromKey(tileKey);
      if (!coord) continue;

      downloadedTiles.push({
        id: Number(region.id),
        z: coord[0],
        x: coord[1],
        y: coord[2],
      });
    }

    applyDownloadedTileSelections(downloadedTiles);
  }

  async function downloadTiles(): Promise<void> {
    if (!canDownloadTiles) {
      return;
    }

    if (isSyncingTileSelection || !hasPendingTileSyncChanges) return;

    isSyncingTileSelection = true;

    try {
      const existingRegions = await listRegions();
      const existingDownloadedByTileKey = new Map<string, number>();

      for (const region of existingRegions) {
        const tileKey = tileKeyFromRegionName(region.name);
        if (!tileKey || !Number.isFinite(region.id)) continue;
        existingDownloadedByTileKey.set(tileKey, Number(region.id));
      }

      const selectedTileKeys = new Set(selectedTiles.keys());

      for (const [tileKey, regionId] of existingDownloadedByTileKey.entries()) {
        if (!selectedTileKeys.has(tileKey)) {
          await deleteRegion(regionId);
        }
      }

      for (const [tileKey, tileCoord] of selectedTiles.entries()) {
        if (existingDownloadedByTileKey.has(tileKey)) {
          continue;
        }

        const tileExtent = tileGrid.getTileCoordExtent(tileCoord);
        const intersection = getIntersection(OREGON_EXTENT, tileExtent);
        const minX = intersection[0];
        const minY = intersection[1];
        const maxX = intersection[2];
        const maxY = intersection[3];
        if (
          minX === undefined ||
          minY === undefined ||
          maxX === undefined ||
          maxY === undefined
        ) {
          continue;
        }

        await createRegion({
          min_x: minX,
          max_x: maxX,
          min_y: minY,
          max_y: maxY,
          name: regionNameFromTileKey(tileKey),
        });
      }

      await loadDownloadedRegions();
    } catch (error: unknown) {
      reportNonVitalError(error, 'SystemDataPage.downloadTiles');
    } finally {
      isSyncingTileSelection = false;
    }
  }

  //gets the version of the app
  async function loadPatchLevelInfo(): Promise<void> {
    try {
      const response = await getLatestVersion();

      const version = response.Version;

      if (version) {
        versionNumber = version.version_number ?? "Unknown";

        gitHash = version.git_hash
          ? version.git_hash.substring(0, 8)
          : "Unknown";

        releaseDate = formatReleaseDate(version.release_date);
      }
    } catch (error) {
      versionLoadFailed = true;
      reportNonVitalError(error, 'SystemDataPage.loadPatchLevelInfo');
    }
  }

  //to format the date for releaseDate
  function formatReleaseDate(dateString: string | null | undefined): string {
    if (!dateString) return "Unknown";

    const date = new Date(dateString);

    if (isNaN(date.getTime())) {
      return dateString;
    }

    return date.toLocaleDateString();
  }
</script>


<div class="translucent-overlay" style="overflow-y: hidden;">

  <!-- this is a box to show the title -->
  <div class="title-box"> 
      <!-- this is the exit button -->
    <BackButton />
    <h2>System Data</h2>

    <SystemIndicators 
      isActiveBackground={false} 
      isRoadDiscoverActive={false}
    />
  </div>

 <div class="body-container">

  <div class="left-column">

  <!-- this contains both the information of the system and import/export button-->
  <div class="seperate-vert">

    <div class="system-info-scroll">

    <!-- this is the information of the system -->
    <div class="seperate-hori">
      <div class="info-box">
        <p class="info-row">
          <span class="info-label">Number of GPS Tracks:</span>
          <span class="info-value">{$trackStore.tracks.length}</span>
        </p>
      </div>
      
      <div class="info-box">
        <p class="info-row">
          <span class="info-label">Current Speed(mph):</span>
          <span class="info-value">{speed_mph.toFixed(1)} mph</span>
        </p>
      </div>
      
      {#if versionLoadFailed}
        <div class="info-box">
          <span class="info-value">Version information unavailable</span>
        </div>
      {/if}

      <div class="info-box">
        <p class="info-row">
          <span class="info-label">Current Patch Level:</span>
          <span class="info-value">{versionNumber}</span>
        </p>
      </div>

      <div class="info-box">
        <p class="info-row">
          <span class="info-label">Git Hash:</span>
          <span class="info-value">{gitHash}</span>
        </p>
      </div>

      <div class="info-box">
        <p class="info-row">
          <span class="info-label">Release Date:</span>
          <span class="info-value">{releaseDate}</span>
        </p>
      </div>

      <div class="info-box">
        <p class="info-row">
          <span class="info-label">Signal Strength:</span>
          {#if $wifiStore.isConnected}
            <span class="info-value">{$wifiStore.signalStrength}%</span>
          {:else}
            <span class="info-value">Disconnected</span>
          {/if}
        </p>
      </div>

      <div class="info-box">
        <p class="info-row">
          <span class="info-label">WiFi Network:</span>
          <span class="info-value">
            {$wifiStore.ssid ?? 'Not Connected'}
          </span>
        </p>
      </div>

      <div class="info-box">
        <p class="info-row">
          <span class="info-label">Maps Downloaded:</span>
          <span class="info-value">{storage_amount_dowloaded}</span>
        </p>
      </div>

      <div class="info-box">
        <p class="info-row">
          <span class="info-label">Storage Left:</span>
          <span class="info-value">{storageRemaining}</span>
        </p>
      </div>
    </div>

    <!-- system health -->
    {#if sysHealth}
      <div class="divider"></div>
      <div class="sys-health">
        <p class="sys-health-title">System Health</p>

        <div class="health-metric">
          <div class="health-metric-header">
            <span>CPU</span>
            <span>{sysHealth.cpu.percent_total.toFixed(1)}% · load {sysHealth.cpu.load_avg_1.toFixed(2)}</span>
          </div>
          <div class="bar">
            <div
              class="bar-fill"
              class:bar-warn={sysHealth.cpu.percent_total >= 70}
              class:bar-danger={sysHealth.cpu.percent_total >= 90}
              style="width:{Math.min(sysHealth.cpu.percent_total, 100)}%"
            ></div>
          </div>
        </div>

        <div class="health-metric">
          <div class="health-metric-header">
            <span>RAM</span>
            <span>{formatBytes(sysHealth.memory.used_bytes)} / {formatBytes(sysHealth.memory.total_bytes)}</span>
          </div>
          <div class="bar">
            <div
              class="bar-fill"
              class:bar-warn={sysHealth.memory.used_percent >= 70}
              class:bar-danger={sysHealth.memory.used_percent >= 90}
              style="width:{Math.min(sysHealth.memory.used_percent, 100)}%"
            ></div>
          </div>
        </div>

        <div class="health-metric">
          <div class="health-metric-header">
            <span>Disk</span>
            <span>{formatBytes(sysHealth.disk.used_bytes)} / {formatBytes(sysHealth.disk.total_bytes)}</span>
          </div>
          <div class="bar">
            <div
              class="bar-fill"
              class:bar-warn={sysHealth.disk.used_percent >= 70}
              class:bar-danger={sysHealth.disk.used_percent >= 90}
              style="width:{Math.min(sysHealth.disk.used_percent, 100)}%"
            ></div>
          </div>
        </div>

        <div class="health-row">
          <span>Net ↓ {formatBytes(sysHealth.network.recv_rate_bytes)}/s · ↑ {formatBytes(sysHealth.network.send_rate_bytes)}/s</span>
          <span>Up {formatUptime(sysHealth.uptime_seconds)}</span>
        </div>
      </div>
    {/if}

    </div>

    <!-- divider -->
    <div class="divider"></div>

    <!-- update section -->
    <div class="update-section">
      {#if updateCheckState === 'idle'}
        <button class="button-color" on:click={handleCheckForUpdates}>
          <img src={check_mark} alt="Check" class="icons" />
          Check for Updates
        </button>
      {:else if updateCheckState === 'checking'}
        <div class="checking-text">Checking for updates...</div>
      {:else if updateCheckState === 'no-updates'}
        <button class="button-color" on:click={handleCheckForUpdates}>
          <img src={check_mark} alt="Check" class="icons" />
          Check for Updates
        </button>
        <div class="no-updates-text">No updates available</div>
      {:else if updateCheckState === 'updates-available'}
        <button class="button-color button-color--update" on:click={handleUpdate}>
          <img src={update_icon} alt="Update" class="icons" />
          Update
        </button>
      {:else if updateCheckState === 'updating'}
        <div class="checking-text">Updating...</div>
      {:else if updateCheckState === 'updated'}
        <button class="button-color" on:click={handleCheckForUpdates}>
          <img src={check_mark} alt="Check" class="icons" />
          Check for Updates
        </button>
        <div class="done-text">Done!</div>
      {/if}       
    </div>
  </div>

  </div>

  <div class="download-box">
    <!-- map controls bar -->
    <div class="map-controls">
      <button
        class="map-ctrl-btn"
        class:map-ctrl-btn--active={isSelectMode}
        disabled={!canDownloadTiles}
        on:click={toggleSelectMode}
      >
        {isSelectMode ? 'Stop Selecting' : 'Select Tiles'}
      </button>

      <button
        class="map-ctrl-btn"
        disabled={!canDownloadTiles || !hasSelection}
        on:click={clearSelection}
      >
        Clear
      </button>

      <span class="zoom-follow-note">Tile size follows map zoom</span>

      <button
        class="map-ctrl-btn map-ctrl-btn--download"
        disabled={!canDownloadTiles || !hasPendingTileSyncChanges || isSyncingTileSelection}
        on:click={downloadTiles}
      >
        <img src={download_icon} alt="Download" class="icons" />
        {isSyncingTileSelection ? 'Saving...' : 'Download Map'}
      </button>
    </div>

    <!-- map/fallback fills the remaining space -->
    <div class="map-stage">
      <div
        class="map-container"
        class:select-mode={isSelectMode}
        class:map-container--hidden={!canDownloadTiles}
        bind:this={mapElement}
      ></div>

      {#if !canDownloadTiles}
        <div class="map-fallback-message">Map downloads require an active Wi-Fi connection.</div>
      {/if}
    </div>
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
    flex-direction: column;
    justify-content: flex-start;
    position: relative;
    padding-left: 2%;
    padding-right: 2%;
    padding-top: 8px;
    padding-bottom: 8px;
    box-sizing: border-box;
    gap: 12px;
    background-color: var(--secondary-color);
    width: 100%;
    flex: 1;
    min-height: 0;
    border-width: 2px;
    border-color: rgb(255, 255, 255);
    border-style: solid;
    overflow: hidden;
  }

  .system-info-scroll {
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 2px;
  }

  .seperate-hori {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    gap: 8px;
    width: 100%;
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

  .divider {
    height: 1px;
    background-color: rgba(0, 0, 0, 0.2);
    width: 100%;
  }

  .update-section {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    width: 100%;
  }

  .checking-text {
    color: rgba(0, 0, 0, 0.7);
    text-align: left;
  }

  .no-updates-text {
    color: rgba(0, 0, 0, 0.7);
    font-size: 0.85rem;
    text-align: left;
    padding-left: 2px;
  }

  .done-text {
    color: rgba(0, 0, 0, 0.7);
    font-size: 0.85rem;
    text-align: left;
    padding-left: 2px;
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

  .map-stage {
    position: relative;
    flex: 1;
    min-height: 0;
    width: 100%;
  }

  .map-container--hidden {
    visibility: hidden;
    pointer-events: none;
  }

  .map-fallback-message {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 16px;
    font-size: 1rem;
    color: rgba(0, 0, 0, 0.8);
    background: rgba(255, 255, 255, 0.35);
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

  .zoom-follow-note {
    font-size: 0.8rem;
    color: rgba(0, 0, 0, 0.75);
    white-space: nowrap;
  }

  .button-color {
    background-color: rgba(188, 188, 188);
    color: black;
    outline: none;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    padding: 8px 16px;
    margin-top: auto;
    cursor: pointer;
  }
  .button-color:hover {
    background-color: rgba(202, 202, 202);
  }
  .button-color--update {
    background-color: rgba(76, 175, 80, 0.9);
    color: white;
    margin-top: 0;
  }
  .button-color--update:hover {
    background-color: rgba(56, 155, 60, 0.9);
  }

  .icons {
    width: 24px;
    height: 24px;
    margin-right: 8px;
  }

  .sys-health {
    display: flex;
    flex-direction: column;
    gap: 6px;
    width: 100%;
  }

  .sys-health-title {
    margin: 0;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: rgba(0, 0, 0, 0.45);
  }

  .health-metric {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .health-metric-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    color: rgba(0, 0, 0, 0.8);
  }

  .health-metric-header span:first-child {
    font-weight: 600;
  }

  .bar {
    width: 100%;
    height: 4px;
    background-color: rgba(0, 0, 0, 0.12);
    border-radius: 2px;
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    width: 0%;
    background-color: rgba(51, 153, 204, 0.85);
    border-radius: 2px;
    transition: width 0.8s ease;
  }

  .bar-fill.bar-warn {
    background-color: rgba(230, 155, 0, 0.9);
  }

  .bar-fill.bar-danger {
    background-color: rgba(210, 50, 50, 0.9);
  }

  .health-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    color: rgba(0, 0, 0, 0.7);
    margin-top: 2px;
  }

</style>
