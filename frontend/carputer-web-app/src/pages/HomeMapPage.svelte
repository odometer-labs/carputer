<script lang="ts">
  import { onMount } from 'svelte';
  import Map from 'ol/Map.js';
  import View from 'ol/View.js';
  import TileLayer from 'ol/layer/Tile.js';
  import OSM from 'ol/source/OSM.js';
  import { fromLonLat } from 'ol/proj.js';
  import Feature from 'ol/Feature.js';
  import Point from 'ol/geom/Point.js';
  import VectorLayer from 'ol/layer/Vector.js';
  import VectorSource from 'ol/source/Vector.js';
  import { Style, Circle, Fill, Stroke } from 'ol/style.js';
  import 'ol/ol.css';
  import { gpsService } from '../fake-api/gpsService';
  import type { GPSPosition } from '../fake-api/types';

  let mapElement: HTMLDivElement | undefined;
  let map: Map | undefined;
  let locationStatus: string = 'Getting location...';
  let userLayer: VectorLayer | undefined;
  let userMarker: Feature<Point> | undefined;
  let latestUserCoords: number[] | null = null;
  let isFollowingUser: boolean = true;
  let isFollowingHeading: boolean = false;
  let latestHeadingDegrees: number | null = null;
  let isProgrammaticMove: boolean = false;
  let hasCenteredInitially: boolean = false;
  let orientationListener: ((event: DeviceOrientationEvent) => void) | null = null;

  onMount(() => {
    loadMap();
    startGPSTracking();

    // Cleanup when component is destroyed
    return () => {
      if (map) {
        map.setTarget(undefined);
      }
      gpsService.stop();
      if (orientationListener) {
        window.removeEventListener('deviceorientationabsolute', orientationListener);
        window.removeEventListener('deviceorientation', orientationListener);
      }
    };
  });

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
      })
    });

    map.on('movestart', () => {
      if (!isProgrammaticMove) {
        isFollowingUser = false;
        isFollowingHeading = false;
      }
    });

    map.on('moveend', () => {
      isProgrammaticMove = false;
    });
  }

  function centerOnUserLocation(zoomToUser: boolean = false): void {
    if (!map || !latestUserCoords) {
      return;
    }

    isProgrammaticMove = true;
    const view = map.getView();
    view.setCenter(latestUserCoords);

    if (zoomToUser) {
      view.setZoom(15);
    }
  }

  function applyHeadingRotation(): void {
    if (!map || !isFollowingUser || !isFollowingHeading || latestHeadingDegrees === null) {
      return;
    }

    const headingRadians = (latestHeadingDegrees * Math.PI) / 180;
    isProgrammaticMove = true;
    map.getView().setRotation(-headingRadians);
  }

  function resetMapRotation(): void {
    if (!map) {
      return;
    }

    isProgrammaticMove = true;
    map.getView().setRotation(0);
  }

  /* Note for startGPSTracking():
    Getting GPS location from the fake API for testing.
    Defaults to mock data but can connect to gpsfake if available.
    Change useMockData to false in gpsService.ts to connect to gpsfake instead.
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

            const vectorSource = new VectorSource({
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
            userMarker.setGeometry(new Point(coords));
          }

          if (!hasCenteredInitially) {
            centerOnUserLocation(true);
            hasCenteredInitially = true;
          } else if (isFollowingUser) {
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

  function snapToUserLocation(): void {
    if (!isFollowingUser) {
      isFollowingUser = true;
      isFollowingHeading = false;
      centerOnUserLocation(true);
      return;
    }

    isFollowingHeading = !isFollowingHeading;

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
        <i class="iconoir-maps-arrow" style="font-size: 24px;"></i>
      {:else}
        <i class="iconoir-compass" style="font-size: 24px;"></i>
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
  /* I need to make this whole button bigger */
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

</style>