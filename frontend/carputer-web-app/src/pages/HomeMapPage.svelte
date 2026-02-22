<script>
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
  import { push } from 'svelte-spa-router';

  let mapElement;
  let map;
  let locationStatus = 'Getting location...';
  let watchId = null;
  let userLayer;
  let orientationListener = null;

  onMount(() => {

    loadMap();
    snapToUserLocation();

    // Cleanup when component is destroyed
    return () => {
      if (map) {
        map.setTarget(null);
      }
      if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
      }
      if (orientationListener) {
        window.removeEventListener('deviceorientationabsolute', orientationListener);
        window.removeEventListener('deviceorientation', orientationListener);
      }
    };
  });

  function loadMap() {
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

  }

/* Note for snapToUserLocation():
  Right now, we are currently getting the user's location from browser data.
  As soon as we can start getting data from the hardware this will need to change.
*/
  export function snapToUserLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lon = position.coords.longitude;
          const lat = position.coords.latitude;
          const coords = fromLonLat([lon, lat]);
          
          // Center map on user's location
          map.getView().setCenter(coords);
          map.getView().setZoom(19); // Zoom in to city level
          
          // Add a marker at the user's location
          const marker = new Feature({
            geometry: new Point(coords)
          });
          
          marker.setStyle(new Style({
            image: new Circle({
              radius: 8,
              fill: new Fill({ color: '#3399CC' }),
              stroke: new Stroke({ color: '#fff', width: 2 })
            })
          }));
          
          const vectorSource = new VectorSource({
            features: [marker]
          });

          if (userLayer) {
            map.removeLayer(userLayer);
          }

          userLayer = new VectorLayer({
            source: vectorSource
          });

          map.addLayer(userLayer);
          
          locationStatus = `Location: ${lat.toFixed(4)}, ${lon.toFixed(4)}`;
          console.log('User location:', lat, lon);
        },
        (error) => {
          console.error('Geolocation error:', error.message);
          locationStatus = 'Location access denied or unavailable';
        },
        {
          enableHighAccuracy: true,
          
          maximumAge: 0
        }
      );
    } else {
      locationStatus = 'Geolocation not supported by browser';
    }
  }

  function goToNewPage() {
    push('/other');
  }


  let isDropdownOpen = false;

</script>

<main style="margin: 0; padding: 0; height: 100%; width: 100%;">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/iconoir-icons/iconoir@main/css/iconoir.css" />
  
  <div class="snap_nav_icon">
      <!-- svelte-ignore a11y_consider_explicit_label -->
    <button class="snap_nav_btn" on:click={snapToUserLocation}><i class="iconoir-maps-arrow" style="font-size: 24px;"></i></button>
  </div>

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


  {#if isDropdownOpen}
    <div class="dropdown-menu">
      <ul style="list-style: none; margin: 0; padding: 10px;">
        <li style="padding: 0;">
            <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false;}}>
              <i class="iconoir-wifi" style="font-size: 16px; margin-right: 8px; color: black"></i>
              Wifi
              <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">Connected</sub>
              </div>  
            </button>
        </li>
        <li style="padding: 0;">
            <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false;}}>
              <i class="iconoir-download" style="font-size: 16px; margin-right: 8px; color: black"></i>
              Download Map
              <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">2GB free</sub>
              </div>  
            </button>
        </li>
        <li style="padding: 0;">
            <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false;}}>
              <i class="iconoir-settings" style="font-size: 16px; margin-right: 8px; color: black"></i>
              Settings
              <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">Day mode activated</sub>
              </div>  
            </button>
        </li>
        <li style="padding: 0;">
          <button class="dropdown-menu_btn" on:click={() => { isDropdownOpen = false;}}>
            <i class="iconoir-info-circle" style="font-size: 16px; margin-right: 8px; color: black"></i>
            System Info
            <div class="grid-container" style="margin-left: 30px; margin-top: 5px;">
                <sub class="sub_text">Patch Level: 0.0.0</sub>
            </div>  
          </button>
        </li>
      </ul>
    </div>
  {/if}

  <div class="temp">
    <button class="temp_btn" on:click={goToNewPage}>New Page</button>
  </div>

  <div class="map-container">
    <div bind:this={mapElement} class="map" style="width: 100%; height: 100%;"></div>
  </div>

</main>


<style>
  .grid-container {
    display: grid;
    grid-template-columns: 1fr 1fr; /* Creates three equal-width columns */
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
    gap: 10px;
  }

  .snap_nav_btn {
    padding: 15px;
    cursor: pointer;
    border: none;
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

  .temp{
    position: absolute;
    bottom: 50px;
    right: 50px;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .temp_btn {
    -webkit-text-fill-color: black;
    padding: 15px;
    cursor: pointer;
    border: none;
    border-radius: 4px;
    background-color: #ffffff;
    color: white;
    font-weight: 500;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    transition: all 0.2s;
    outline: none;
  }

  .hamburger_menu_icon {
    position: absolute;
    top: 20px;
    right: 25px;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .hamburger_menu_icon_btn {
    padding: 15px;
    cursor: pointer;
    border: none;
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
    background: white;
    border: 1px solid #ccc; 
    border-radius: 4px; 
    box-shadow: 0 2px 6px rgba(0,0,0,0.2); 
    background-color: rgba(188, 188, 188, 0.9);
    z-index: 1000;
  }

  .dropdown-menu_btn {
    -webkit-text-fill-color: black;
    padding: 8px 12px; 
    cursor: pointer; 
    border: none; 
    background: none; 
    width: 100%; 
    text-align: left;
    background-color: rgba(188, 188, 188, 0.9);
    outline: none;
  }
  .dropdown-menu_btn:hover {
    background-color: rgb(202, 202, 202);
  }


</style>