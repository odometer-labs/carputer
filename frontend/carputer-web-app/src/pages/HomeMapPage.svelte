<script lang="ts">
  import { onMount } from 'svelte';
  import { derived } from 'svelte/store';
  import Map from 'ol/Map.js';
  import View from 'ol/View.js';
  import TileLayer from 'ol/layer/Tile.js';
  import OSM from 'ol/source/OSM.js';
  import { defaults as defaultControls } from 'ol/control/defaults.js';
  import { fromLonLat } from 'ol/proj.js';
  import Feature from 'ol/Feature.js';
  import Point from 'ol/geom/Point.js';
  import LineString from 'ol/geom/LineString.js'
  import VectorLayer from 'ol/layer/Vector.js';
  import VectorSource from 'ol/source/Vector.js';
  import { Style, Circle, Fill, Stroke, RegularShape, Icon, Text } from 'ol/style.js';
  import 'ol/ol.css';
  import { getCurrentPosition, subscribeToPositionStream, getAprsStations } from '../api/restApi';
  import type { GPSData, APRSStation } from '../api/types';
  import { push, location } from 'svelte-spa-router';
  import { Cluster } from 'ol/source';
  import { reportNonVitalError, reportVitalError } from '../stores/errorStore';
  import { settingsPreferences, type TrackRange } from '../services/settings_preferences';
  import aprsIconUrl from '../assets/icons/aprs-bold.svg';
  import userArrowIconUrl from '../assets/icons/maps-arrow-blue-white.svg';
  import { trackStore } from '../stores/trackStore'
  import '../assets/styles/ui.css'; // this is for styling the overlay ui (settings page, etc)
  import SystemIndicators from "../assets/components/SystemIndicators.svelte";
  import NameTrackPopUp from '../assets/components/NameTrackPopUp.svelte';
  import APRSPopUp from '../assets/components/APRSPopUp.svelte';
  import type { Track, LineString as ApiLineString } from '../api/types';

  let mapElement: HTMLDivElement | undefined;
  let map: Map | undefined;
  let locationStatus: string = 'Getting location...';

  // roadhistory and current track line
  let oldTrackLayer: VectorLayer | undefined;
  let oldTrackSource: VectorSource | undefined;
  let currentTrackLayer: VectorLayer | undefined;
  let currentTrackSource: VectorSource | undefined;
  let currentTrackFeature: Feature<LineString> | undefined;

  // this is to store the tracks points to be sent to backend
  let trackCoords: [number, number][] = [];
  let trackName: string;
  let startTime: Date;

  //APRS locations
  let aprsLayer: VectorLayer | undefined;
  let aprCluster: Cluster | undefined;
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
  let aprsRefreshInterval: ReturnType<typeof setInterval> | null = null;

  let zoomLevel: number = 18;
  $: zoomLevel = $settingsPreferences.defaultZoom; // default zoom level when centering on user

  //this is to prevent having too many calls for $trackStore.checkIfNewRoad
  let lastCheckTime: number = 0;
  const CHECK_ROAD_INTERVAL: number = 1000; //one second

  // for the popup window to set the name
  let showTrackNamePopup: boolean = false;
  let pendingFinalize: boolean = false;

  // this is used to prevent the user track having too many points on 1 spot
  let lastUserTrackCoord: [number, number] | null = null;
  let lastRoadHistoryCoord: [number, number] | null = null;

  const GPS_JITTER_DISTANCE_METERS = 4;
  const GPS_STATIONARY_SPEED_MPS = 0.8;
  const ROAD_HISTORY_MIN_DISTANCE_METERS = 8;

  // this is the list of tracks that is shown on the page, filtered
  const filteredTracks = derived(
    [trackStore, settingsPreferences],
    ([$trackStore, $settingsPreferences]) => {
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

      return {
        tracks: $trackStore.tracks.filter(track => {
          const start = new Date(track.start_time);

          //this is for after the date
          if ((afterDate) && (start < afterDate)) return false;

          return true;
        }),
        selectedTrackId: $trackStore.selectedTrackId
      };
    }
  );

  // this function gets the date by 1 day, week, month or year. 
  // if there shouldn't be a date, if the user has selected all tracks
  // to show then it should default to null
  function getAfterDate(range: TrackRange) : Date | null {
    if (range === "all") return null;

    const date = new Date();

    // set to midnight
    date.setHours(0, 0, 0, 0);

    switch (range) {
      case "day":
        date.setDate(date.getDate() - 1);
        break;
      case "week":
        date.setDate(date.getDate() - 7);
        break;
      case "month":
        date.setMonth(date.getMonth() - 1);
        break;
      case "year":
        date.setFullYear(date.getFullYear() - 1);
        break;
    }

    return date;
  }

  function getUserIconScale(): number {
    return 0.6 + ($settingsPreferences.iconSizeLevel * 0.2);
  }

  function getUserMarkerRadius(): number {
    return 5 + $settingsPreferences.iconSizeLevel;
  }

  function hexToRgba(hex: string, alpha: number): string {
    const normalized = hex.trim().replace("#", "");

    if (!/^[0-9a-fA-F]{6}$/.test(normalized)) {
      return `rgba(255, 52, 241, ${alpha})`;
    }

    const red = parseInt(normalized.slice(0, 2), 16);
    const green = parseInt(normalized.slice(2, 4), 16);
    const blue = parseInt(normalized.slice(4, 6), 16);

    return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
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

  // run once when the Svelte component is mounted
  onMount(() => {
    try {
      loadMap();             // create map instance and hook events
      startGPSTracking();    // begin receiving backend GPS data
    } catch (error: unknown) {
      reportVitalError(error, 'HomeMapPage.onMount');
    }

    // Load APRS stations from backend and refresh periodically.
    loadAprsStations();
    aprsRefreshInterval = setInterval(() => {
      loadAprsStations();
    }, 15000);

    // subscribes to track changes
    const unsubscribeTracks = filteredTracks.subscribe(({ tracks, selectedTrackId }) => {
      renderTracks(tracks, selectedTrackId);
    });
    // Load completed tracks from backend.
    trackStore.loadTracks();

    return () => {
      unsubscribeTracks();

      map?.setTarget(undefined);
      stopGPSSubscription?.();
      stopGPSSubscription = null;

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
    };
  });

  /**
   * Initialize the OpenLayers map and attach all event handlers.
   * Distinguishes user pan (breaks lock) from pinch-zoom (keeps lock) via
   * active touch pointer tracking, and guards programmatic view changes with
   * isProgrammaticMove / isProgrammaticRotationChange flags.
   */
  function loadMap(): void {
    map = new Map({
      target: mapElement,
      layers: [
        new TileLayer({
          source: new OSM() // OpenStreetMap tiles
        })
      ],
      view: new View({
        center: fromLonLat([-122.6765, 45.5231]), // Default center: Portland, OR (fallback when GPS is unavailable)
        zoom: zoomLevel
      }),
      controls: defaultControls({
        rotate: false, // disable default rotation control since we handle it ourselves
      })
    });

    // ------this is the track layer----------
    oldTrackSource = new VectorSource();

    // this determines the color/shape/size of the old tracks
    oldTrackLayer = new VectorLayer({
      source: oldTrackSource,
      minZoom: 13,
      style: (feature) => {
        const isActive = feature.get('isActive');

        return new Style({
          stroke: new Stroke({
            color: isActive ? getSelectedTrackColor(0.95) : getRestingTrackColor(0.55),
            width: isActive ? getTrackWidth(1) : getTrackWidth(0)
          })
        })
      }
    });

    currentTrackSource = new VectorSource();

    // this determines the color/shape/size of the current track the user is making
    currentTrackLayer = new VectorLayer({
      source: currentTrackSource,
      style: () => new Style({
        stroke: new Stroke({
          color: getSelectedTrackColor(0.8),
          width: getTrackWidth(0)
        })
      })
    });

    map.addLayer(oldTrackLayer);
    map.addLayer(currentTrackLayer);

    // this is for making points for APRS locations ------------
    aprsSource = new VectorSource();

    aprCluster = new Cluster({
      distance: 30, // this is what determines how far from each point before combining.
      source: aprsSource
    });

    aprsLayer = new VectorLayer({
      source: aprCluster,
      minZoom: 13, //this determines how far our zoomed can the aprs still load.
      style: (feature) => {
        // make sure that map exists before doing anything
        if (!map) return;

        const size = feature.get('features').length;

        // Single point = normal APRS icon
        if (size === 1) {
          const inner = feature.get('features')[0] as Feature | undefined;
          const aprsId = inner?.get('aprsId') as string | undefined;
          const isSelected = aprsId !== undefined && aprsPopupData?.aprsId === aprsId;
          return getAprsPinStyle(getAprsIcon(), isSelected);
        }

        // Cluster (circle with number, combined close by points)
        return new Style({
          image: new Circle({
            radius: 12,
            fill: new Fill({ color: '#3399CC' }),
            stroke: new Stroke({ color: '#fff', width: 2 })
          }),
          text: new Text({
            text: size.toString(),
            fill: new Fill({ color: '#fff' })
          })
        });
      }
    });

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
  function startGPSTracking(): void {
    getCurrentPosition()
      .then((position) => handleGPSPosition(position))
      .catch((error: unknown) => {
        const message = `Initial GPS fetch failed: ${String(error)}`;
        locationStatus = message;
        console.warn('GPS unavailable — map defaulting to Portland, OR');
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

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      return;
    }

    if (typeof position.heading === 'number' && Number.isFinite(position.heading)) {
      latestHeadingDegrees = position.heading;
    }

    const coords = fromLonLat([lon, lat]) as [number, number];
    const speedMps = Number(position.speed);

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

    if (!map) {
      return;
    }

    // use the coord from the user to add it to the current users track line
    applyTrackLine(filteredCoords, lon, lat);

    // checks if the current road is a new road or not.
    checkRoadHistory(filteredCoords);

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

  // this function checks if the user has passed a certain amount of distance
  // I made this becuase I realized that the applyTrackLine will add multiple 
  // points on the same spot on the map and that just seem very wastefull.
  function hasMovedEnough(newCoords : [number, number], minimumDistance = 5) : boolean {
    if (!lastUserTrackCoord) return true;

    const dx = newCoords[0] - lastUserTrackCoord[0];
    const dy = newCoords[1] - lastUserTrackCoord[1];

    return (Math.sqrt(dx * dx + dy * dy) > minimumDistance);
  }

  // this is used to make the track line for the user, given that the coordnates pushed
  // in are the user's coordinates.
  async function applyTrackLine(
    coords : [number, number],
    lon: number,
    lat: number
  ) : Promise<void> {
    // this adds a line so the user can see where they have been (current track) 
    if ($trackStore.isTracking) { 

      //this determines if this is the beggining of a new line 
      if (!currentTrackFeature) { 
        currentTrackFeature = new Feature({
          geometry: new LineString([coords])
        }); 
        
        currentTrackSource?.addFeature(currentTrackFeature);
        
        lastUserTrackCoord = coords;

        trackCoords = [[lon, lat]];
        return;
      } 

      // adds a point to an existing track line
      if (hasMovedEnough(coords as [number, number])){ 
        const geom = currentTrackFeature.getGeometry();
        if (geom) {
          geom.appendCoordinate(coords);
          lastUserTrackCoord = coords;

          trackCoords.push([lon, lat])
        }
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

  function getDistanceMeters(a: [number, number], b: [number, number]): number {
    const dx = a[0] - b[0];
    const dy = a[1] - b[1];
    return Math.sqrt(dx * dx + dy * dy);
  }


  // set up the old tracks that the user has been on previously
  function renderTracks(tracks: Track[], selectedTrackId: number | null) : void {
    //check if the trackSource exists
    if (!oldTrackSource) return;

    // remove any of the old tracks on the map to prevent duplicates
    oldTrackSource.clear();

    tracks.forEach((track) => {
      const coords = track.geom.coordinates.map(([lon, lat]) =>
        fromLonLat([lon, lat])
      );

      const feature = new Feature({
        geometry: new LineString(coords),
        trackId: track.track_id
      });

      feature.set("isActive", track.track_id === selectedTrackId)

      oldTrackSource?.addFeature(feature);
    });
  }

  // this function helps start the tracking for backend and end
  // it also refreshes the TrackLayer from the current track when the user 
  // presses end track
  async function startEndTracking() : Promise<void> {
    if ($trackStore.isTracking) {
      //open the popup before stopping the track
      trackName = "";
      showTrackNamePopup = true;
      pendingFinalize = true;
      return;
    } else {
      startTime = new Date();
      trackCoords = []; //just to make sure it's empty
      await trackStore.start();
    }
  }

  
  // for handling the naming of a track with the popup
  // Called by NameTrackPopUp confirm event
  async function confirmTrackNameFromPopup(name: string): Promise<void> {
    if (!pendingFinalize) return;
    trackName = name;
    await finalizeTrack(trackName);
    await trackStore.end();
    currentTrackSource?.clear();
    currentTrackFeature = undefined;
    await trackStore.loadTracks();
    showTrackNamePopup = false;
    pendingFinalize = false;
  }

  //in case the user wishes to cancel ending the track or naming
  function cancelTrackName(): void {
    showTrackNamePopup = false;
    pendingFinalize = false;
  }

  // this puts the trackCoords into a LineString type to be put into back end DB
  async function finalizeTrack(customTrackName: string) {
    //must have atleast 2 points
    if (trackCoords.length < 2) {
      trackCoords = [];
      return;
    }

    const lineString: ApiLineString= {
      type: "LineString",
      coordinates: trackCoords,
    };

    const res = await trackStore.addTrack(lineString);

    trackCoords = [];
    
    if (res === null) return;

    //set the name and correct time
    const track = {
      start_time: startTime.toISOString(),
      end_time: new Date().toISOString(),
      track_name: customTrackName,
    }

    await trackStore.updateTrack(res, track)
  }


  // TODO: there are appearently many different kinds of aprs icons so it may need
  // to be able to shift through different icons for the situation. or if we decided
  // to not implement different icons for different aprs then that fine, just remove
  // this comment.
  function getAprsIcon(): string {
    return aprsIconUrl;
  }

  /**
   * Sets up feature points for APRS stations fetched from the backend API.
   */
  function addAprsPoint(lat: number, long: number, callsign: string, comment: string | null): void {
    //if the aprsSource hasn't been set up then don't do anything
    if (!aprsSource) return;

    const aprsId = `${callsign}-${lat.toFixed(6)}-${long.toFixed(6)}`;

    const aprsMarker = new Feature({
      geometry: new Point(fromLonLat([long, lat])),
      aprsId,
      callsign,
      comment,
    });

    aprsSource.addFeature(aprsMarker);
  }

  // this is the style for the pins, you can insert the image to the pin
  function getAprsPinStyle(img: string, isSelected: boolean = false): Style[] {
    return [
      // pin stem (triangle)
      new Style({
        image: new RegularShape({
          points: 3,
          radius: 10,
          rotation: Math.PI,
          fill: new Fill({ color: 'black' }),
          stroke: new Stroke({ color: 'black', width: 1 }),
          displacement: [0, -12]
        })
      }),

      // pin head (circle)
      new Style({
        image: new Circle({
          radius: 13,
          fill: new Fill({ color: isSelected ? '#93e38b' : 'white' }),
          stroke: new Stroke({ color: 'black', width: 2 }),
          displacement: [0, 26]
        })
      }),

      // APRS icon on top
      new Style({
        image: new Icon({
          src: img,
          scale: 0.05,
          anchor: [0.5, 0.5],
          displacement: [0, 26]
        })
      })
    ];
  }

  //This is just for testing purposes and eventually will be removed when we get APRS data
  // this gets a random location near the user and sends that information to the addAprsPoint()
  // to make a aprs feature point.
  async function loadAprsStations(): Promise<void> {
    if (!$settingsPreferences.areAprsPointsOn) {
      aprsSource?.clear();
      return;
    }

    try {
      let stations: APRSStation[] = await getAprsStations();

      // If nothing is nearby, widen the search radius to show available APRS traffic.
      if (stations.length === 0) {
        stations = await getAprsStations(500000);
      }

      aprsSource?.clear();
      stations.forEach((station) => {
        addAprsPoint(station.latitude, station.longitude, station.callsign, station.last_comment ?? null);
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

  // APRS popup: set when the user clicks a single APRS station on the map
  let aprsPopupData: { aprsId: string; callsign: string; comment: string | null } | null = null;
</script>

<main style="margin: 0; padding: 0; height: 100%; width: 100%;">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/iconoir-icons/iconoir@main/css/iconoir.css" />
  
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
                <sub class="sub_text">Connected to PSU-Guest</sub>
              </div>  
            </button>
        </li>
        <li style="padding: 0;">
            <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false; goToSettingPreference()}}>
              <i class="iconoir-settings dropdown-menu_btn_icons"></i>
              Settings
              <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">Day mode activated</sub>
              </div>  
            </button>
        </li>
        <li style="padding: 0;">
          <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false; goToDashboard()}}>
            <i class="iconoir-info-circle dropdown-menu_btn_icons"></i>
            System Data
            <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">Patch Level: 0.0.0</sub>
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
    pendingFinalize={pendingFinalize}
    initialTrackName={trackName}
    on:confirm={e => confirmTrackNameFromPopup(e.detail.trackName)}
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