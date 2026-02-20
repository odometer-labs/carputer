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

</script>

<div class="map-container">
  <div bind:this={mapElement} class="map" style="width: 100%; height: 100%;"></div>
</div>

<style>
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
</style>