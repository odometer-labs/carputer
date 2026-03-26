<script lang="ts">
  import { onMount } from 'svelte';
  import Map from 'ol/Map.js';
  import View from 'ol/View.js';
  import TileLayer from 'ol/layer/Tile.js';
  import OSM from 'ol/source/OSM.js';
  import { defaults as defaultControls } from 'ol/control/defaults.js';
  import { fromLonLat, toLonLat } from 'ol/proj.js';
  import Feature from 'ol/Feature.js';
  import Point from 'ol/geom/Point.js';
  import VectorLayer from 'ol/layer/Vector.js';
  import VectorSource from 'ol/source/Vector.js';
  import { Style, Circle, Fill, Stroke, RegularShape, Icon } from 'ol/style.js';
  import 'ol/ol.css';
  import { gpsService } from '../fake-api/gpsService';
  import type { GPSPosition } from '../fake-api/types';
  import { push } from 'svelte-spa-router';

  import '../assets/styles/ui.css'; // this is for styling the overlay ui (settings page, etc)
  import SystemIndicators from "../assets/components/SystemIndicators.svelte";

  let mapElement: HTMLDivElement | undefined;
  let map: Map | undefined;
  let locationStatus: string = 'Getting location...';

  //APRS locations
  let aprsLayer: VectorLayer | undefined;
  let aprsSource: VectorSource | undefined;

  // position marker objects
  let userLayer: VectorLayer | undefined;
  let userMarker: Feature<Point> | undefined;
  let vectorSource: VectorSource | undefined;

  // latest GPS state (map projection coords + heading)
  let latestUserCoords: number[] | null = null;
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

  let zoomLevel: number = 18; // default zoom level when centering on user

  // run once when the Svelte component is mounted
  onMount(() => {
    loadMap();             // create map instance and hook events
    startGPSTracking();    // begin receiving simulated GPS data

    // this will be removed in the future but for now this sets up 10 aprs points around the 
    // the user, to display an aprs icon.
    const interval = setInterval(() => {
    if (!latestUserCoords) return;

    for (let i = 0; i < 10; i++) {
      setRandomAprsPoints();
    }

    clearInterval(interval); // run once
  }, 500);

    return () => {
      map?.setTarget(undefined);
      gpsService.stop();

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
        center: fromLonLat([0, 0]), // Default center
        zoom: zoomLevel
      }),
      controls: defaultControls({
        rotate: false, // disable default rotation control since we handle it ourselves
      })
    });

    // this is for making points for APRS locations
    aprsSource = new VectorSource();
    aprsLayer = new VectorLayer({
      source: aprsSource
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

      if (!isProgrammaticMove && (isFollowingUser || isFollowingHeading)) {
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
    return '/src/assets/icons/maps-arrow-blue-white.svg';
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
          scale: 1,
          rotation: (latestHeadingDegrees * Math.PI) / 180,
          rotateWithView: true,
          crossOrigin: 'anonymous',
        })
      }));
    } else {
      userMarker.setStyle(new Style({
        image: new Circle({
          radius: 8,
          fill: new Fill({ color: '#3399CC' }),
          stroke: new Stroke({ color: '#fff', width: 2 })
        })
      }));
    }
  }

  /**
   * Start receiving positions from the GPS service (NMEA playback or gpsfake).
   * Each update: stores coords and heading, creates/moves the marker feature,
   * recentres the map if locked, and applies heading rotation in compass mode.
   * See src/fake-api/README.md for mode switching and configuration.
   */
  function startGPSTracking(): void {
    gpsService.start(
      (position: GPSPosition) => {
        const lon: number = position.longitude;
        const lat: number = position.latitude;
        if (typeof position.heading === 'number' && Number.isFinite(position.heading)) {
          latestHeadingDegrees = position.heading;
        }
        const coords = fromLonLat([lon, lat]);
        latestUserCoords = coords;
        
        if (map) {
          if (!userMarker) {
            // first fix: create marker feature and add to map
            userMarker = new Feature({
              geometry: new Point(coords)
            });

            userMarker.setStyle(new Style({
              image: new Circle({
                radius: 8,
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
              source: vectorSource
            });

            map.addLayer(userLayer);
          } else {
            // subsequent fixes: move marker and refresh style
            const geometry = userMarker.getGeometry();
            if (geometry) {
              geometry.setCoordinates(coords);
            } else {
              userMarker.setGeometry(new Point(coords));
            }
            
            if (isFollowingUser) {
              updateUserMarkerStyle();
            }
            
            if (vectorSource) {
              vectorSource.changed();
            }
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
      },
      (error: string) => {
        console.error('GPS error:', error);
        locationStatus = `GPS Error: ${error}`;
      }
    );
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

  // TODO: there are appearently many different kinds of aprs icons so it may need
  // to be able to shift through different icons for the situation. or if we decided
  // to not implement different icons for different aprs then that fine, just remove
  // this comment.
  function getAprsIcon(): string {
    return '/src/assets/aprs-bold.svg';
  }

  /**
   * Sets up feature points for APRS points, this isn't ment to be the final
   * version. it simply is putting points onto the map. 
   * in the future we should make it so that the points can be updated.
   */
  function addAprsPoint(lat: number, long: number): void {
    //if the aprsSource hasn't been set up then don't do anything
    if (!aprsSource) return;

    //create marker feature and add to map
    // make the point(feature) using lat and long
    const aprsMarker = new Feature({
      geometry: new Point(fromLonLat([long, lat]))
    });

    aprsMarker.setStyle(new Style({
      image: new Icon({
        src: getAprsIcon(),
        scale: 0.07,
        anchor: [0.5, 1]
      })
    }));

    aprsSource.addFeature(aprsMarker);
  }

  //This is just for testing purposes and eventually will be removed when we get APRS data
  // this gets a random location near the user and sends that information to the addAprsPoint()
  // to make a aprs feature point.
  function setRandomAprsPoints(): void{
    if (!latestUserCoords) return;

    const coords = toLonLat(latestUserCoords); //gets the coordnates

    const long = coords[0];
    const lat = coords[1];

    if (lat === undefined || long === undefined) return; //makes sure it isn't null

    addAprsPoint(
      lat + (Math.random() - 0.5)* 0.01,
      long + (Math.random() - 0.5)* 0.01
    );
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
    push("/Dashboard");
  }
  
  // this function changes route to /Dashboard
  function goToMapDownload() : void {
    push("/MapDownload");
  }

  let isDropdownOpen: boolean = false;
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
            <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false; goToMapDownload()}}>
              <i class="iconoir-download dropdown-menu_btn_icons"></i>
              Download Map
              <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">2GB free</sub>
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
            System Info
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



  <div class="map-container">
    <div bind:this={mapElement} class="map" style="width: 100%; height: 100%;"></div>
  </div>

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

</style>