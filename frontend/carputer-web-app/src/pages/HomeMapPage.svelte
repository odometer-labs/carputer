<script lang="ts">
  import { onMount } from 'svelte';
  import { derived, writable, get } from 'svelte/store';
  import Map from 'ol/Map.js';
  import View from 'ol/View.js';
  import TileLayer from 'ol/layer/Tile.js';
  import { defaults as defaultControls } from 'ol/control/defaults.js';
  import { fromLonLat } from 'ol/proj.js';
  import Feature from 'ol/Feature.js';
  import Point from 'ol/geom/Point.js';
  import LineString from 'ol/geom/LineString.js';
  import VectorLayer from 'ol/layer/Vector.js';
  import VectorSource from 'ol/source/Vector.js';
  import { Style, Circle, Fill, Stroke, Icon} from 'ol/style.js';
  import 'ol/ol.css';
  import { getCurrentPosition, subscribeToPositionStream, getAprsStations, subscribeToSysHealth } from '../api/restApi';
  import { getCurrentWifiConnection, getWifiAccessPoints } from '../api/wifiApi';
  import type { GPSData, APRSStation, SysHealthData } from '../api/types';
  import { push, location } from 'svelte-spa-router';
  import { Cluster } from 'ol/source';
  import { reportNonVitalError, reportVitalError, setNonVitalErrorSuppressed } from '../stores/errorStore';
  import { setWifiConnected, setWifiDisconnected, setWifiPower, wifiStore } from '../stores/wifiStore';
  import { settingsPreferences } from '../services/settings_preferences';
  import userArrowIconUrl from '../assets/icons/maps-arrow-blue-white.svg';
  import { trackStore } from '../stores/trackStore'
  import '../assets/styles/ui.css'; // this is for styling the overlay ui (settings page, etc)
  import SystemIndicators from "../assets/components/SystemIndicators.svelte";
  import NameTrackPopUp from '../assets/components/NameTrackPopUp.svelte';
  import APRSPopUp from '../assets/components/APRSPopUp.svelte';
  import { isTrackWithinRadius, hexToRgba, getDistanceMeters } from '../utils/mapUtils';
  import { createBaseTileSource } from '../services/map/tileSource';
  import { addAprsPoint, createAprsLayer, } from '../services/map/aprsLayer';
  import { createTrackLayers, renderTracks } from '../services/map/trackRenderer';
  import { getAfterDate } from '../utils/dateUtils';

  let mapElement: HTMLDivElement | undefined;
  let map: Map | undefined;
  let isBootstrapping: boolean = true;
  let hasInitialGpsFix: boolean = false;
  let resolveFirstGpsFix: (() => void) | null = null;
  let locationStatus: string = 'Getting location...';
  let baseTileLayer: TileLayer | undefined;
  let usingOnlineTiles: boolean = false;
  let hasResolvedWifiStatus: boolean = false;

  // roadhistory and current track line
  let oldTrackLayer: VectorLayer | undefined;
  let oldTrackSource: VectorSource | undefined;
  let currentTrackLayer: VectorLayer | undefined;
  let currentTrackSource: VectorSource | undefined;
  let currentTrackFeature: Feature<LineString> | undefined;

  // This is the name of what the track will be set as.
  let trackName: string = "";

  //APRS locations
  let aprsLayer: VectorLayer | undefined;
  let aprsCluster: Cluster | undefined;
  let aprsSource: VectorSource | undefined;

  // position marker objects
  let userLayer: VectorLayer | undefined;
  let userMarker: Feature<Point> | undefined;
  let vectorSource: VectorSource | undefined;

  // latest GPS state (map projection coords + heading)
  let latestUserCoords: [number, number] | null = null;
  let latestHeadingDegrees: number | null = null;

  // follow-lock state: position only vs. position + heading (compass mode)
  let isFollowingUser: boolean = true;
  let isFollowingHeading: boolean = false;

  // guards that prevent user-gesture handlers from reacting to our own view changes
  let isProgrammaticMove: boolean = false;
  let hasCenteredInitially: boolean = false;
  let isProgrammaticRotationChange: boolean = false;
  let rotationProgrammaticGuardTimeout: ReturnType<typeof setTimeout> | null = null;

  // active touch pointer IDs — used to distinguish one-finger pan from pinch-zoom
  let activeTouchPointerIds: Set<number> = new Set();
  let pointerDownListener: ((event: PointerEvent) => void) | null = null;
  let pointerUpListener: ((event: PointerEvent) => void) | null = null;

  // device orientation listener (reserved for future compass integration)
  let orientationListener: ((event: DeviceOrientationEvent) => void) | null = null;
  let stopGPSSubscription: (() => void) | null = null;
  let stopSysHealthSubscription: (() => void) | null = null;
  let aprsRefreshInterval: ReturnType<typeof setInterval> | null = null;

  let zoomLevel: number = 18;
  $: zoomLevel = $settingsPreferences.defaultZoom; // default zoom level when centering on user

  //this is to prevent having too many calls for $trackStore.checkIfNewRoad
  let lastCheckTime: number = 0;
  const CHECK_ROAD_INTERVAL: number = 1000; //one second

  // for the popup window to set the name
  let showTrackNamePopup: boolean = false;
  let pendingStart: boolean = false;

  // this is used to prevent the user track having too many points on 1 spot
  let lastUserTrackCoord: [number, number] | null = null;
  let lastRoadHistoryCoord: [number, number] | null = null;

  const GPS_JITTER_DISTANCE_METERS = 4;
  const GPS_STATIONARY_SPEED_MPS = 0.8;
  const ROAD_HISTORY_MIN_DISTANCE_METERS = 8;
  const TRACK_POINT_MIN_DISTANCE_METERS = 5;
  const MILES_TO_METERS = 1609.34;
  const userLonLat = writable<[number, number] | null>(null);

  // this is the list of tracks that is shown on the page, filtered
  const filteredTracks = derived(
    [trackStore, settingsPreferences, userLonLat],
    ([$trackStore, $settingsPreferences, $userLonLat]) => {
      //disable all tracks 
      if (!$settingsPreferences.areAllTracksOn) {
        //set the selectedTrackID to null
        $trackStore.selectedTrackId = null;

        //return just an empty tracks
        return {
          tracks: [],
          selectedTrackId: $trackStore.selectedTrackId
        };
      }

      const afterDate = getAfterDate($settingsPreferences.trackRange);
      const radiusMeters = $settingsPreferences.milesToDiscoverRoads * MILES_TO_METERS;

      return {
        tracks: $trackStore.tracks.filter(track => {
          const start = new Date(track.start_time);

          //this is for after the date
          if ((afterDate) && (start < afterDate)) return false;

          // Apply the frontend-only radius filter from the current user location.
          if ($userLonLat && !isTrackWithinRadius(track, $userLonLat, radiusMeters)) {
            return false;
          }

          return true;
        }),
        selectedTrackId: $trackStore.selectedTrackId
      };
    }
  );


  function getUserIconScale(): number {
    return 0.6 + ($settingsPreferences.iconSizeLevel * 0.2);
  }

  function getUserMarkerRadius(): number {
    return 5 + $settingsPreferences.iconSizeLevel;
  }

  function getSelectedTrackColor(alpha: number = 1): string {
    return hexToRgba($settingsPreferences.selectedTrackColor, alpha);
  }

  function getRestingTrackColor(alpha: number = 1): string {
    return hexToRgba($settingsPreferences.restingTrackColor, alpha);
  }

  function getTrackWidth(offset: number = 0): number {
    return Math.max(1, $settingsPreferences.trackThickness + offset);
  }

  function bytesToGigabytes(bytes: number): number {
    return bytes / 1_073_741_824;
  }

  $: if (oldTrackLayer) {
    $settingsPreferences.selectedTrackColor;
    $settingsPreferences.restingTrackColor;
    $settingsPreferences.trackThickness;
    oldTrackLayer.changed();
  }

  $: if (currentTrackLayer) {
    $settingsPreferences.selectedTrackColor;
    $settingsPreferences.restingTrackColor;
    $settingsPreferences.trackThickness;
    currentTrackLayer.changed();
  }

  // HomeMapPage remains mounted under overlay routes; clear popup when leaving map route.
  $: if ($location !== '/' && aprsPopupData !== null) {
    aprsPopupData = null;
  }

  $: if (aprsLayer) {
    aprsLayer.setVisible($settingsPreferences.areAprsPointsOn);
    aprsPopupData;
    aprsLayer.changed();
  }

  $: if (!$settingsPreferences.areAprsPointsOn && aprsPopupData !== null) {
    aprsPopupData = null;
  }

  // Use online tiles only when Wi-Fi is both powered and connected.
  // Otherwise prefer local tiles for offline operation.
  $: if (baseTileLayer) {
    const shouldUseOnlineTiles = !hasResolvedWifiStatus || ($wifiStore.isWifiOn && $wifiStore.isConnected);
    if (shouldUseOnlineTiles !== usingOnlineTiles) {
      usingOnlineTiles = shouldUseOnlineTiles;
      baseTileLayer.setSource(createBaseTileSource(usingOnlineTiles));
    }
  }

  // run once when the Svelte component is mounted
  onMount(() => {
    setNonVitalErrorSuppressed(true);

    try {
      startSystemHealthTracking(); // subscribe to live system health for menu hints
      void startGPSTracking();    // begin receiving backend GPS data

      // Keep startup silent until first GPS fix and initial service calls complete.
      void Promise.allSettled([
        initializeWifiStateForMap(),
        loadAprsStations(),
        waitForFirstGpsFix(),
      ]).finally(() => {
        isBootstrapping = false;
        setNonVitalErrorSuppressed(false);
      });
    } catch (error: unknown) {
      reportVitalError(error, 'HomeMapPage.onMount');
      isBootstrapping = false;
      setNonVitalErrorSuppressed(false);
    }

    // Refresh APRS stations periodically after the initial startup load.
    aprsRefreshInterval = setInterval(() => {
      loadAprsStations();
    }, 15000);

    // subscribes to track changes
    const unsubscribeTracks = filteredTracks.subscribe(({ tracks, selectedTrackId }) => {
      if (!oldTrackSource) return;

      renderTracks(oldTrackSource, tracks, selectedTrackId);
    });
    // Load completed tracks from backend.
    trackStore.loadTracks();

    return () => {
      unsubscribeTracks();

      map?.setTarget(undefined);
      stopGPSSubscription?.();
      stopGPSSubscription = null;
      stopSysHealthSubscription?.();
      stopSysHealthSubscription = null;

      if (orientationListener) {
        window.removeEventListener('deviceorientationabsolute', orientationListener);
        window.removeEventListener('deviceorientation', orientationListener);
      }

      if (mapElement && pointerDownListener && pointerUpListener) {
        mapElement.removeEventListener('pointerdown', pointerDownListener);
        mapElement.removeEventListener('pointerup', pointerUpListener);
        mapElement.removeEventListener('pointercancel', pointerUpListener);
      }

      if (rotationProgrammaticGuardTimeout !== null) {
        clearTimeout(rotationProgrammaticGuardTimeout);
      }

      if (aprsRefreshInterval !== null) {
        clearInterval(aprsRefreshInterval);
        aprsRefreshInterval = null;
      }

      setNonVitalErrorSuppressed(false);
    };
  });

  function waitForFirstGpsFix(): Promise<void> {
    if (hasInitialGpsFix) {
      return Promise.resolve();
    }

    return new Promise((resolve) => {
      resolveFirstGpsFix = resolve;
    });
  }

  /**
   * Initialize the OpenLayers map and attach all event handlers.
   * Distinguishes user pan (breaks lock) from pinch-zoom (keeps lock) via
   * active touch pointer tracking, and guards programmatic view changes with
   * isProgrammaticMove / isProgrammaticRotationChange flags.
   */
  function loadMap(): void {
    usingOnlineTiles = !hasResolvedWifiStatus || ($wifiStore.isWifiOn && $wifiStore.isConnected);
    const initialCenter = latestUserCoords ?? fromLonLat([0, 0]);

    baseTileLayer = new TileLayer({
      source: createBaseTileSource(usingOnlineTiles),
    });

    map = new Map({
      target: mapElement,
      layers: [
        baseTileLayer
      ],
      view: new View({
        center: initialCenter,
        zoom: zoomLevel
      }),
      controls: defaultControls({
        rotate: false, // disable default rotation control since we handle it ourselves
      })
    });

    // ------this is the track layer----------
    const trackLayers = createTrackLayers(
      getSelectedTrackColor,
      getRestingTrackColor,
      getTrackWidth
    );

    oldTrackLayer = trackLayers.oldTrackLayer;
    oldTrackSource = trackLayers.oldTrackSource;

    currentTrackLayer = trackLayers.currentTrackLayer;
    currentTrackSource = trackLayers.currentTrackSource;

    map.addLayer(oldTrackLayer);
    map.addLayer(currentTrackLayer);

    const { tracks, selectedTrackId } = get(filteredTracks);
    if (oldTrackSource){
      renderTracks(oldTrackSource, tracks, selectedTrackId);
    }

    // APRS layer
    const aprsObjects = createAprsLayer(
      () => aprsPopupData?.aprsId
    );

    aprsLayer = aprsObjects.layer;
    aprsSource = aprsObjects.source;
    aprsCluster = aprsObjects.cluster;

    map.addLayer(aprsLayer);

    if (mapElement) {
      pointerDownListener = (event: PointerEvent) => {
        if (event.pointerType === 'touch') {
          activeTouchPointerIds.add(event.pointerId);
        }
      };

      pointerUpListener = (event: PointerEvent) => {
        if (event.pointerType === 'touch') {
          activeTouchPointerIds.delete(event.pointerId);
        }
      };

      mapElement.addEventListener('pointerdown', pointerDownListener);
      mapElement.addEventListener('pointerup', pointerUpListener);
      mapElement.addEventListener('pointercancel', pointerUpListener);
    }

    // one-finger drag breaks lock; two-finger pinch does not
    map.on('pointerdrag', () => {
      if (activeTouchPointerIds.size >= 2) return;

      // User intent always wins: dragging should immediately release follow-lock.
      if (isFollowingUser || isFollowingHeading) {
        isFollowingUser = false;
        isFollowingHeading = false;
        updateUserMarkerStyle();
        resetMapRotation();
      }
    });

    map.on('moveend', () => {
      isProgrammaticMove = false;
    });

    // manual map rotation exits compass mode but keeps position lock
    map.getView().on('change:rotation', () => {
      if (isProgrammaticRotationChange) return;

      if (isFollowingHeading) {
        isFollowingHeading = false;
        updateUserMarkerStyle();
      }
    });

    map.on('singleclick', (event) => {
      // Handle track selection clicks
      map?.forEachFeatureAtPixel(event.pixel, (featureLike) => {
        if (!(featureLike instanceof Feature)) return;

        const trackId = featureLike.get('trackId');
        if (trackId != null) {
          trackStore.selectTrack(trackId);
        }
      },
      {
        layerFilter: (layer) => layer === oldTrackLayer,
        hitTolerance: 13
      });

      // Handle APRS station clicks — only show popup for single (non-clustered) points
      let hitAprs = false;
      map?.forEachFeatureAtPixel(event.pixel, (featureLike) => {
        if (!(featureLike instanceof Feature)) return;

        const clusteredFeatures = featureLike.get('features') as Feature[] | undefined;
        if (!clusteredFeatures || clusteredFeatures.length !== 1) return;

        const inner = clusteredFeatures[0];
        if (!inner) return;
        const aprsId = inner?.get('aprsId') as string | undefined;
        const callsign = inner?.get('callsign') as string | undefined;
        if (callsign && aprsId) {
          aprsPopupData = {
            aprsId,
            callsign,
            comment: inner.get('comment') ?? null
          };
          hitAprs = true;
        }
      },
      {
        layerFilter: (layer) => layer === aprsLayer,
        hitTolerance: 10
      });

      if (!hitAprs) {
        aprsPopupData = null;
      }
    });
  }

  async function initializeWifiStateForMap(): Promise<void> {
    try {
      const [currentConnection, accessPoints] = await Promise.all([
        getCurrentWifiConnection(),
        getWifiAccessPoints(),
      ]);

      if (!currentConnection) {
        setWifiDisconnected();
        return;
      }

      setWifiPower(true);
      const matchingAccessPoint = accessPoints.find(
        (accessPoint) => accessPoint.ssid === currentConnection.ssid,
      );
      setWifiConnected(currentConnection.ssid, matchingAccessPoint?.signal_strength ?? 0);
    } catch (error: unknown) {
      reportNonVitalError(error, 'HomeMapPage.initializeWifiStateForMap');
    } finally {
      hasResolvedWifiStatus = true;
    }
  }


  /**
   * Move the map view to the user's latest coordinates.
   *
   * @param zoomToUser when true, perform a smooth animation including zoom;
   *                   otherwise just jump the center (used for continuous
   *                   tracking so animations don't stack up).
   */
  function centerOnUserLocation(zoomToUser: boolean = false): void {
    if (!map || !latestUserCoords) {
      return;
    }

    isProgrammaticMove = true; // suppress movestart handler reaction
    const view = map.getView();
    
    if (zoomToUser) {
      view.cancelAnimations();
      view.animate({ center: latestUserCoords, zoom: zoomLevel, duration: 500 });
    } else {
      // Set immediately — avoids queuing up animations on rapid GPS updates
      view.setCenter(latestUserCoords);
    }
  }

  /**
   * Rotate the map to match the user's heading (compass mode).
   * Only active when both isFollowingUser and isFollowingHeading are true.
   * In simple-follow mode the map stays north-up and the marker rotates instead.
   */
  function applyHeadingRotation(): void {
    if (!map || !isFollowingUser || !isFollowingHeading || latestHeadingDegrees === null) {
      return;
    }

    const headingRadians = (-latestHeadingDegrees * Math.PI) / 180;
    isProgrammaticMove = true;
    beginProgrammaticRotationGuard();
    map.getView().setRotation(headingRadians);
  }

  /** Animate the map back to north-up. Called when exiting compass mode. */
  function resetMapRotation(): void {
    if (!map) return;

    isProgrammaticMove = true;
    beginProgrammaticRotationGuard(350);
    map.getView().setRotation(0);
    map.getView().animate({ rotation: 0, duration: 300 });
  }

  /** Suppress the change:rotation handler for durationMs after a programmatic rotation. */
  function beginProgrammaticRotationGuard(durationMs: number = 50): void {
    isProgrammaticRotationChange = true;
    if (rotationProgrammaticGuardTimeout !== null) clearTimeout(rotationProgrammaticGuardTimeout);
    rotationProgrammaticGuardTimeout = setTimeout(() => {
      isProgrammaticRotationChange = false;
      rotationProgrammaticGuardTimeout = null;
    }, durationMs);
  }


  function getIconoirArrowUrl(): string {
    return userArrowIconUrl;
  }

  /**
   * Update the position marker style to reflect current tracking state.
   *
   * When locked on the user with a heading, renders a directional arrow SVG.
   * rotateWithView:true lets OpenLayers apply the current view rotation every
   * render frame, so the arrow stays correct during live map rotation without
   * needing style updates on each change:rotation event.
   *
   * Falls back to a plain blue circle when not locked or heading is unknown.
   */
  function updateUserMarkerStyle(): void {
    if (!userMarker) return;

    if (isFollowingUser && latestHeadingDegrees !== null) {
      userMarker.setStyle(new Style({
        image: new Icon({
          src: getIconoirArrowUrl(),
          anchor: [0.5, 0.5],
          scale: getUserIconScale(),
          rotation: (latestHeadingDegrees * Math.PI) / 180,
          rotateWithView: true,
          crossOrigin: 'anonymous',
        })
      }));
    } else {
      userMarker.setStyle(new Style({
        image: new Circle({
          radius: getUserMarkerRadius(),
          fill: new Fill({ color: '#3399CC' }),
          stroke: new Stroke({ color: '#fff', width: 2 })
        })
      }));
    }
  }

  /**
   * Start receiving positions from backend API.
   * Pulls one initial snapshot then subscribes to /ws/get-position updates.
   */
  async function startGPSTracking(): Promise<void> {
    await getCurrentPosition()
      .then((position) => handleGPSPosition(position))
      .catch((error: unknown) => {
        // Keep startup resilient: websocket updates can still provide the first valid fix.
        locationStatus = 'Waiting for GPS fix...';
        reportNonVitalError(error, 'HomeMapPage.getCurrentPosition');
      });

    stopGPSSubscription = subscribeToPositionStream(
      (position: GPSData) => {
        handleGPSPosition(position);
      },
      (error: string) => {
        console.error('GPS error:', error);
        locationStatus = `GPS Error: ${error}`;
        reportNonVitalError(error, 'HomeMapPage.subscribeToPositionStream');
      }
    );
  }

  function handleGPSPosition(position: GPSData): void {
    const lon: number = Number(position.longitude);
    const lat: number = Number(position.latitude);
    const speedMps = Number(position.speed);

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      return;
    }

    // gpsd and some upstreams emit 0/0 placeholders before a real fix is available.
    if (lat === 0 && lon === 0) {
      return;
    }

    if (typeof position.heading === 'number' && Number.isFinite(position.heading)) {
      latestHeadingDegrees = position.heading;
    }

    const coords = fromLonLat([lon, lat]) as [number, number];

    let filteredCoords: [number, number] = coords;
    if (latestUserCoords) {
      const movementMeters = getDistanceMeters(coords, latestUserCoords);
      const isLikelyStationary = Number.isFinite(speedMps) && speedMps < GPS_STATIONARY_SPEED_MPS;

      // Hold position when stationary to suppress GPS drift jitter on the marker.
      if (isLikelyStationary && movementMeters < GPS_JITTER_DISTANCE_METERS) {
        filteredCoords = latestUserCoords;
      }
    }

    latestUserCoords = filteredCoords;
    userLonLat.set([lon, lat]);

    if (!hasInitialGpsFix) {
      hasInitialGpsFix = true;

      if (!map) {
        loadMap();
      }

      resolveFirstGpsFix?.();
      resolveFirstGpsFix = null;
    }

    if (!map) {
      return;
    }

    if (!userMarker) {
      // first fix: create marker feature and add to map
      userMarker = new Feature({
        geometry: new Point(filteredCoords)
      });

      userMarker.setStyle(new Style({
        image: new Circle({
          radius: getUserMarkerRadius(),
          fill: new Fill({ color: '#3399CC' }),
          stroke: new Stroke({ color: '#fff', width: 2 })
        })
      }));

      vectorSource = new VectorSource({
        features: [userMarker]
      });

      if (userLayer) {
        map.removeLayer(userLayer);
      }

      userLayer = new VectorLayer({
        source: vectorSource,
        updateWhileAnimating: true,
        updateWhileInteracting: true
      });

      map.addLayer(userLayer);
      map.render();
    } else {
      // subsequent fixes: move marker and refresh style
      const geometry = userMarker.getGeometry();
      if (geometry) {
        geometry.setCoordinates(filteredCoords);
      } else {
        userMarker.setGeometry(new Point(filteredCoords));
      }

      if (isFollowingUser) {
        updateUserMarkerStyle();
      }

      if (vectorSource) {
        vectorSource.changed();
      }

      // Request a redraw so marker motion remains visible during map drag interactions.
      map.render();
    }

    if (!hasCenteredInitially) {
      centerOnUserLocation(true);
      hasCenteredInitially = true;
    } else if (isFollowingUser) {
      centerOnUserLocation(false);
    }

    applyHeadingRotation();

    locationStatus = `Location: ${lat.toFixed(4)}, ${lon.toFixed(4)}`;

    // Non-critical side effects should never block primary GPS rendering.
    try {
      applyTrackLine(filteredCoords);
      checkRoadHistory(filteredCoords);
    } catch (error: unknown) {
      reportNonVitalError(error, 'HomeMapPage.handleGPSPosition.sideEffects');
    }
  }

  /**
   * Handler for the teleport/compass button in the UI.
   * - if we are currently not tracking, start following the user and
   *   zoom to 15.
   * - if we are already following, toggle the heading-follow state.
   *   Turning heading-follow on causes the map to rotate; turning it off
   *   resets the map to north-up and rotates the marker.
   */
  function snapToUserLocation(): void {
    map?.getView().setZoom(zoomLevel);
    if (!isFollowingUser) {
      isFollowingUser = true;
      isFollowingHeading = false;
      updateUserMarkerStyle();
      centerOnUserLocation(true);
      resetMapRotation();
      return;
    }

    isFollowingHeading = !isFollowingHeading;
    updateUserMarkerStyle();

    if (isFollowingHeading) {
      applyHeadingRotation();
    } else {
      resetMapRotation();
    }
  }


  // this is used to make the track line for the user, given that the coordnates pushed
  // in are the user's coordinates.
  function applyTrackLine(coords : [number, number]): void {
    // this adds a line so the user can see where they have been (current track) 
    if ($trackStore.isTracking) { 

      //this determines if this is the beggining of a new line 
      if (!currentTrackFeature) { 
        currentTrackFeature = new Feature({
          geometry: new LineString([coords])
        }); 
        
        currentTrackSource?.addFeature(currentTrackFeature);
        
        lastUserTrackCoord = coords;

        return;
      } 

      if ( 
        lastUserTrackCoord && getDistanceMeters(coords, lastUserTrackCoord) 
        < TRACK_POINT_MIN_DISTANCE_METERS
      ) {
        return;
      }

      // adds a point to an existing track line
      const geom = currentTrackFeature.getGeometry();
      if (geom) {
        geom.appendCoordinate(coords);
        lastUserTrackCoord = coords;
      }
    }
  }

  // this function is used to check if the current road the user is on is a road
  // that the user has never driven on before.
  function checkRoadHistory(coords: [number, number]) : void {
    const now = Date.now();

    // makes sure that the most a call for checking if the road is new is at most 1 per sec
    if (now - lastCheckTime <= CHECK_ROAD_INTERVAL) return;

    if (lastRoadHistoryCoord) {
      const movementMeters = getDistanceMeters(coords, lastRoadHistoryCoord);
      if (movementMeters < ROAD_HISTORY_MIN_DISTANCE_METERS) return;
    }

    lastCheckTime = now;
    lastRoadHistoryCoord = [coords[0], coords[1]];
    trackStore.checkIfNewRoad();
  }


  // this function helps start the tracking for backend and end
  // it also refreshes the TrackLayer from the current track when the user 
  // presses end track
  async function startEndTracking() : Promise<void> {
    if ($trackStore.isTracking) {
      await trackStore.end();

      currentTrackSource?.clear();
      currentTrackFeature = undefined;

      await trackStore.loadTracks();
    } else {
      showTrackNamePopup = true;
      pendingStart = true;
    }
  }

  
  // for handling the naming of a track with the popup
  // Called by NameTrackPopUp confirm event
  async function startTrackingNameIt(name: string): Promise<void> {
    if (!pendingStart) return;
    trackName = "";

    await trackStore.start(name);

    showTrackNamePopup = false;
    pendingStart = false;
  }

  //in case the user wishes to cancel ending the track or naming
  function cancelTrackName(): void {
    trackName = "";
    showTrackNamePopup = false;
    pendingStart = false;
  }

  
  async function loadAprsStations(): Promise<void> {
    if (!$settingsPreferences.areAprsPointsOn) {
      aprsSource?.clear();
      return;
    }

    const source = aprsSource;
    if (!source) return;

    source.clear();

    try {
      let stations: APRSStation[] | null = await getAprsStations();

      // If nothing is nearby, widen the search radius to show available APRS traffic.
      if (!stations || stations.length === 0) {
        stations = await getAprsStations(500000);
      }

      stations?.forEach((station) => {
        addAprsPoint(source, station.latitude, station.longitude, station.callsign, station.last_comment ?? null);
      });
    } catch (error: unknown) {
      reportNonVitalError(error, 'HomeMapPage.loadAprsStations');
    }
  }

  // this function changes route to /SettingPreference
  function goToSettingPreference() : void {
    push("/SettingPreference");
  }

  // this function changes route to /Wifi
  function goToWifi() : void {
    push("/Wifi");
  }

  // this function changes route to /Dashboard
  function goToDashboard() : void {
    push("/SystemData");
  }

  let isDropdownOpen: boolean = false;

  let latestSysHealth: SysHealthData | null = null;
  let wifiMenuHint: string = 'Checking Wi-Fi...';
  let settingsMenuHint: string = 'Day mode activated';
  let systemDataMenuHint: string = 'Free storage unavailable';

  $: wifiMenuHint = getWifiMenuHint();
  $: settingsMenuHint = $settingsPreferences.nightMode ? 'Night mode activated' : 'Day mode activated';
  $: systemDataMenuHint = getSystemDataMenuHint(latestSysHealth);

  // APRS popup: set when the user clicks a single APRS station on the map
  let aprsPopupData: { aprsId: string; callsign: string; comment: string | null } | null = null;

  function getSystemDataMenuHint(sysHealth: SysHealthData | null): string {
    if (!sysHealth) {
      return 'Free storage unavailable';
    }

    const freeGb = Math.max(0, bytesToGigabytes(sysHealth.disk.free_bytes));
    return `${freeGb.toFixed(1)} GB free`;
  }

  function getWifiMenuHint(): string {
    if (!hasResolvedWifiStatus) {
      return 'Checking Wi-Fi...';
    }

    if (!$wifiStore.isWifiOn) {
      return 'Wi-Fi is off';
    }

    if ($wifiStore.isConnected) {
      return `Connected to ${$wifiStore.ssid ?? 'network'}`;
    }

    return 'Not connected';
  }

  function startSystemHealthTracking(): void {
    stopSysHealthSubscription = subscribeToSysHealth(
      (data: SysHealthData) => {
        latestSysHealth = data;
      },
      (error: string) => {
        reportNonVitalError(error, 'HomeMapPage.subscribeToSysHealth');
      }
    );
  }
</script>

<main style="margin: 0; padding: 0; height: 100%; width: 100%;">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/iconoir-icons/iconoir@main/css/iconoir.css" />

  {#if isBootstrapping}
    <div class="startup-overlay" role="status" aria-live="polite">Starting up...</div>
  {/if}
  
  <div class="snap_nav_icon">
      <!-- svelte-ignore a11y_consider_explicit_label -->
    <button class="snap_nav_btn" on:click={snapToUserLocation}>
      {#if !isFollowingUser || isFollowingHeading}
        <i class="iconoir-maps-arrow" style="font-size: 28px;"></i>
      {:else}
        <i class="iconoir-compass" style="font-size: 28px;"></i>
      {/if}
    </button>
  </div>

  <!-- This is the button to toggle the hamburger menu -->
  <div class="hamburger_menu_icon">
      <!-- svelte-ignore a11y_consider_explicit_label -->
    <button class="hamburger_menu_icon_btn" on:click={() => isDropdownOpen = !isDropdownOpen}>
      {#if isDropdownOpen}
        <i class="iconoir-xmark" style="font-size: 24px;"></i>
      {:else}
        <i class="iconoir-menu" style="font-size: 24px;"></i>
      {/if}
    </button>
  </div>

  <!-- If the hamburger menu is toggled open then show this menu -->
  {#if isDropdownOpen}
    <div class="dropdown-menu">
      <ul style="list-style: none; margin: 0; padding: 10px;">
        <li style="padding: 0;">
            <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false; goToWifi()}}>
              <i class="iconoir-wifi dropdown-menu_btn_icons"></i>
              Wifi
              <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">{wifiMenuHint}</sub>
              </div>  
            </button>
        </li>
        <li style="padding: 0;">
            <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false; goToSettingPreference()}}>
              <i class="iconoir-settings dropdown-menu_btn_icons"></i>
              Settings
              <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">{settingsMenuHint}</sub>
              </div>  
            </button>
        </li>
        <li style="padding: 0;">
          <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false; goToDashboard()}}>
            <i class="iconoir-info-circle dropdown-menu_btn_icons"></i>
            System Data
            <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">{systemDataMenuHint}</sub>
            </div>  
          </button>
        </li>
      </ul>
    </div>
  {/if}

  
  <!-- this is the system indicators. -->
  <SystemIndicators />

  <!-- this is the button for letting backend know when to start/end a track-->
  <button 
    class="start-end-track_butn"
    on:click={() => startEndTracking()}
    style="background-color: {$trackStore.isTracking ? 'lightcoral' : 'lightgreen'}"
  >
    <strong>{$trackStore.isTracking ? "Stop Track" : "Start Track"}</strong>
  </button>

  <div class="map-container">
    <div bind:this={mapElement} class="map" style="width: 100%; height: 100%;"></div>
  </div>

  <APRSPopUp
    show={aprsPopupData !== null}
    aprsData={aprsPopupData}
    on:close={() => aprsPopupData = null}
  />

  <NameTrackPopUp
    show={showTrackNamePopup}
    initialTrackName={trackName}
    on:confirm={e => startTrackingNameIt(e.detail.trackName)}
    on:cancel={cancelTrackName}
  />
</main>


<style>
  .grid-container {
    display: grid;
    grid-template-columns: 1fr; /* Creates three equal-width columns */
    gap: 10px; /* Adds space between columns */
  }

  .sub_text {
    -webkit-text-fill-color: grey;
    float: right; 
    font-size: 12px; 
    color: gray;
  }

  .map-container {
    width: 100%;
    height: 100%;
  }
  .map {
    width: 100%;
    height: 500px;
    border: 2px solid #ccc;
    border-radius: 4px;
  }
  
  .snap_nav_icon {
    position: absolute;
    bottom: 20px;
    left: 25px;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 10px;
  }
  .snap_nav_btn {
    width: 60px;
    height: 60px;
    padding: 0px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border: 1px solid white;
    border-radius: 50%;
    background-color: rgba(188, 188, 188, 0.9);
    color: #333;
    font-weight: 500;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);   
    transition: all 0.2s;
    outline: none;
  }
  .snap_nav_btn:hover {
    background-color: rgb(225, 225, 225);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
  }

  .hamburger_menu_icon {
    position: absolute;
    top: 20px;
    right: 25px;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 10px;
  }
  .hamburger_menu_icon_btn {
    padding: 0px;
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border: 1px solid white;
    border-radius: 50%;
    background-color: rgba(188, 188, 188, 0.9);
    color: #333;
    font-weight: 500;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    transition: all 0.2s;
    outline: none;
  }
  .hamburger_menu_icon_btn:hover {
    background-color: rgb(225, 225, 225);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
  }

  .dropdown-menu {
    position: absolute; 
    top: 95px; 
    right: 20px; 
    background-color: rgb(188, 188, 188);
    border: 1px solid #ccc; 
    border-radius: 4px; 
    box-shadow: 0 2px 6px rgba(0,0,0,0.2); 
    z-index: 1000;
  }
  .dropdown-menu_btn {
    -webkit-text-fill-color: black;
    padding: 10px 70px 10px 10px;
    cursor: pointer; 
    border: none; 
    background: transparent;
    width: 100%; 
    text-align: left;
    outline: none;
    z-index: 1000;
  }
  .dropdown-menu_btn:hover {
    background-color: rgba(202, 202, 202);
  }
  .dropdown-menu_btn_icons {
    font-size: 20px; 
    margin-right: 8px; 
    position: relative;
    top: 4px;
    color: black;
    font-weight: bold;
  }

  .snap_nav_btn i,
  .hamburger_menu_icon_btn i {
    display: block;
    line-height: 1;
  }

  .start-end-track_butn {
    position: absolute;
    bottom: 20px;
    right: 25px;
    z-index: 1000;
    width: 80px;
    height: 70px;
    padding: 0px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border: 1px solid white;
    border-radius: 15%;
    background-color: rgba(188, 188, 188, 0.9);
    color: #333;
    font-weight: 500;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    transition: all 0.2s;
    outline: none;
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

  :global(.ol-zoom) {
    font-size: 1.1em;
  }

</style>
