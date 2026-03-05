<script lang="ts">
  import { onMount } from 'svelte';
  import Map from 'ol/Map.js';
  import View from 'ol/View.js';
  import TileLayer from 'ol/layer/Tile.js';
  import OSM from 'ol/source/OSM.js';
  import { defaults as defaultControls } from 'ol/control/defaults.js';
  import { fromLonLat } from 'ol/proj.js';
  import Feature from 'ol/Feature.js';
  import Point from 'ol/geom/Point.js';
  import VectorLayer from 'ol/layer/Vector.js';
  import VectorSource from 'ol/source/Vector.js';
  import { Style, Circle, Fill, Stroke, RegularShape, Icon } from 'ol/style.js';
  import 'ol/ol.css';
  import { gpsService } from '../fake-api/gpsService';
  import type { GPSPosition } from '../fake-api/types';

  // references to DOM and OpenLayers objects
  let mapElement: HTMLDivElement | undefined;          // container div bound by Svelte
  let map: Map | undefined;                            // OpenLayers Map instance

  // status text shown somewhere in the UI (not currently rendered)
  let locationStatus: string = 'Getting location...';

  // layers and features used for the user's position marker
  let userLayer: VectorLayer | undefined;
  let userMarker: Feature<Point> | undefined;
  let vectorSource: VectorSource | undefined;

  // latest coordinates (in view projection) and heading from GPS feed
  let latestUserCoords: number[] | null = null;
  let latestHeadingDegrees: number | null = null;

  // tracking state flags triggered by user interaction or code
  let isFollowingUser: boolean = true;        // are we locked to the user's position?
  let isFollowingHeading: boolean = false;    // if true also rotate map to heading

  // helper flags for distinguishing programmatic moves vs. user pan/zoom
  let isProgrammaticMove: boolean = false;
  let hasCenteredInitially: boolean = false;
  let isProgrammaticRotationChange: boolean = false;
  let rotationProgrammaticGuardTimeout: ReturnType<typeof setTimeout> | null = null;

  // touch tracking: allows pinch-zoom without breaking follow lock
  let activeTouchPointerIds: Set<number> = new Set();
  let pointerDownListener: ((event: PointerEvent) => void) | null = null;
  let pointerUpListener: ((event: PointerEvent) => void) | null = null;

  // optional orientation listener reference (not currently used)
  let orientationListener: ((event: DeviceOrientationEvent) => void) | null = null;

  // run once when the Svelte component is mounted
  onMount(() => {
    loadMap();             // create map instance and hook events
    startGPSTracking();    // begin receiving simulated GPS data

    // Cleanup closure returned by onMount: called when component is destroyed
    return () => {
      if (map) {
        map.setTarget(undefined); // remove map from DOM
      }
      gpsService.stop();          // stop fake GPS polling
      if (orientationListener) {
        // remove any attached device orientation listeners
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
   * Initialize the OpenLayers map and attach event handlers.
   *
   * - Creates a basic map with OSM tiles and a default view.
  * - Tracks active touch pointers so we can distinguish one-finger pan
  *   (break lock) from two-finger pinch zoom (keep lock).
  * - Uses pointerdrag/moveend to distinguish user-driven movement from
  *   programmatic recenter/rotation updates.
   */
  function loadMap(): void {
    // Create the map
    map = new Map({
      target: mapElement,
      layers: [
        new TileLayer({
          source: new OSM() // OpenStreetMap tiles
        })
      ],
      view: new View({
        center: fromLonLat([0, 0]), // Default center
        zoom: 2
      }),
      controls: defaultControls({
        rotate: false, // disable default rotation control since we handle it ourselves
      })
    });

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

    // break lock only when the user drags/pans the map
    map.on('pointerdrag', () => {
      const isPinchGesture = activeTouchPointerIds.size >= 2;
      if (isPinchGesture) {
        return;
      }

      if (!isProgrammaticMove && (isFollowingUser || isFollowingHeading)) {
        isFollowingUser = false;
        isFollowingHeading = false;
        updateUserMarkerStyle(); // show circle instead of arrow
        resetMapRotation(); // point map north if we were heading-following
      }
    });

    // clear the programmatic move flag once motion finishes
    map.on('moveend', () => {
      isProgrammaticMove = false;
    });

    // if user manually rotates while in compass mode, drop back to simple follow.
    // no need to call updateUserMarkerStyle() here — rotateWithView:true makes OL
    // apply the current view rotation every render frame automatically.
    map.getView().on('change:rotation', () => {
      if (isProgrammaticRotationChange) {
        return;
      }

      if (isFollowingHeading) {
        isFollowingHeading = false;
        updateUserMarkerStyle(); // switch button icon state
      }
    });

    // intentionally do not break lock on wheel/pinch zoom
    // users can zoom while still following their position
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
      // Cancel any existing animations to ensure a fresh start
      view.cancelAnimations();
      view.animate({
        center: latestUserCoords,
        zoom: 15,
        duration: 500
      });
    } else {
      // For continuous tracking, set the center immediately without animation
      // This prevents animations from queuing up when GPS updates arrive rapidly
      view.setCenter(latestUserCoords);
    }
  }

  /**
   * Rotate the map view to match the user's heading (compass north-up).
   * This only runs when tracking both user and heading; in locked-on mode
   * but heading-off we leave the map north-up and rotate the marker instead.
   */
  function applyHeadingRotation(): void {
    if (!map || !isFollowingUser || !isFollowingHeading || latestHeadingDegrees === null) {
      return;
    }
    
    const headingRadians = (-latestHeadingDegrees * Math.PI) / 180;
    isProgrammaticMove = true;
    beginProgrammaticRotationGuard();
    // Set rotation immediately without animation to stay in sync with rapid GPS updates
    map.getView().setRotation(headingRadians);
  }

  /**
   * Return the map to north-up orientation with a small animation.
   * Called when the user toggles heading-follow off.
   */
  function resetMapRotation(): void {
    if (!map) {
      return;
    }

    isProgrammaticMove = true;
    beginProgrammaticRotationGuard(350);

    // point map toward the north
    map.getView().setRotation(0);

    map.getView().animate({
      rotation: 0,
      duration: 300
    });
  }

  /**
   * Temporarily ignore rotation-change events triggered by our own code.
   */
  function beginProgrammaticRotationGuard(durationMs: number = 50): void {
    isProgrammaticRotationChange = true;

    if (rotationProgrammaticGuardTimeout !== null) {
      clearTimeout(rotationProgrammaticGuardTimeout);
    }

    rotationProgrammaticGuardTimeout = setTimeout(() => {
      isProgrammaticRotationChange = false;
      rotationProgrammaticGuardTimeout = null;
    }, durationMs);
  }


  // utility returning the path to the locally hosted arrow SVG used for
  // the user marker.  switching the returned string lets you easily swap
  // designs without touching the rest of the drawing code.
  function getIconoirArrowUrl(): string {
    // path is relative to the site root once the app is built
    return '/src/assets/icons/maps-arrow-blue-white.svg';
  }

  /**
   * Adjust the style of the position marker based on tracking state.
   *
   * - when following the user with a heading available, render an arrow SVG
   *   oriented appropriately (map rotates in heading-follow mode; marker
   *   rotates in north-up lock mode).
   * - otherwise fall back to a simple blue circle.
   */
  function updateUserMarkerStyle(): void {
    if (!userMarker) {
      return;
    }

    if (isFollowingUser && latestHeadingDegrees !== null) {
      // Show heading arrow while locked on user.
      // rotateWithView: true means OL adds the current view rotation to this value
      // on every render frame, so the arrow stays correct in real-time as the map
      // rotates without needing to update the style on each rotation event.
      // Formula is the same for both compass and non-compass modes:
      //   pixelRotation = (H * π/180) + viewRotation
      // In compass mode viewRotation = -H*π/180, so pixelRotation = 0 (points up). ✓
      // In non-compass mode pixelRotation = H*π/180 + viewRotation as desired. ✓
      const iconUrl = getIconoirArrowUrl();
      const markerRotation = (latestHeadingDegrees * Math.PI) / 180;
      
      userMarker.setStyle(new Style({
        image: new Icon({
          src: iconUrl,
          anchor: [0.5, 0.5],
          scale: 1,
          rotation: markerRotation,
          rotateWithView: true,
          crossOrigin: 'anonymous',
        })
      }));
    } else {
      // Show regular circle marker
      userMarker.setStyle(new Style({
        image: new Circle({
          radius: 8,
          fill: new Fill({ color: '#3399CC' }),
          stroke: new Stroke({ color: '#fff', width: 2 })
        })
      }));
    }
  }

  
  /* Note for startGPSTracking():
    Getting GPS location from the fake API for testing.
    Defaults to mock data but can connect to gpsfake if available.
    Change useMockData to false in gpsService.ts to connect to gpsfake instead.
  */
  /**
   * Start receiving positions from the fake GPS service.
   * Every update drives several pieces of state:
   *  - convert lon/lat to map projection and store in latestUserCoords
   *  - remember heading if available
   *  - create or move the marker feature and refresh its style
   *  - optionally recentre/zoom the map for tracking
   *  - apply map rotation when heading-following
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
            // first GPS fix: create feature, layer and style
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
            // subsequent fixes: move existing feature and refresh style
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
            // on first fix zoom in
            centerOnUserLocation(true);
            hasCenteredInitially = true;
          } else if (isFollowingUser) {
            // on later fixes just recenter without animation
            centerOnUserLocation(false);
          }

          applyHeadingRotation();
          
          locationStatus = `Location: ${lat.toFixed(4)}, ${lon.toFixed(4)}`;
          // console.log('GPS Position:', lat, lon);
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
    map?.getView().setZoom(15);
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
            <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false;}}>
              <i class="iconoir-wifi dropdown-menu_btn_icons"></i>
              Wifi
              <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">Connected to PSU-Guest</sub>
              </div>  
            </button>
        </li>
        <li style="padding: 0;">
            <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false;}}>
              <i class="iconoir-download dropdown-menu_btn_icons"></i>
              Download Map
              <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">2GB free</sub>
              </div>  
            </button>
        </li>
        <li style="padding: 0;">
            <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false;}}>
              <i class="iconoir-settings dropdown-menu_btn_icons"></i>
              Settings
              <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">Day mode activated</sub>
              </div>  
            </button>
        </li>
        <li style="padding: 0;">
          <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false;}}>
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