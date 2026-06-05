import OSM from 'ol/source/OSM.js';
import ImageTile from 'ol/ImageTile.js';


//const for tileSource
const LOCAL_TILE_URL = 'http://localhost:8070/tile/{z}/{x}/{y}.png';
const TRANSPARENT_TILE_DATA_URL = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==';
const TILE_FETCH_TIMEOUT_MS = 10000;

export function createBaseTileSource(useOnlineTiles: boolean): OSM {
  if (useOnlineTiles) {
    return new OSM();
  }

  return new OSM({
    url: LOCAL_TILE_URL,
    wrapX: false,
    crossOrigin: 'anonymous',
    tileLoadFunction: (tile, src) => {
      const imageTile = tile as ImageTile;
      const image = imageTile.getImage();
      if (!(image instanceof HTMLImageElement)) {
        return;
      }
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, TILE_FETCH_TIMEOUT_MS);

      void fetch(src, { signal: controller.signal })
        .then((response) => {
          if (!response.ok || response.status === 204) {
            return null;
          }

          return response.blob();
        })
        .then((blob) => {
          if (!blob) {
            image.src = TRANSPARENT_TILE_DATA_URL;
            return;
          }

          const objectUrl = URL.createObjectURL(blob);
          image.onload = () => {
            URL.revokeObjectURL(objectUrl);
            image.onload = null;
            image.onerror = null;
          };
          image.onerror = () => {
            URL.revokeObjectURL(objectUrl);
            image.onload = null;
            image.onerror = null;
            image.src = TRANSPARENT_TILE_DATA_URL;
          };
          image.src = objectUrl;
        })
        .catch(() => {
          image.onload = null;
          image.onerror = null;
          image.src = TRANSPARENT_TILE_DATA_URL;
        })
        .finally(() => {
          clearTimeout(timeoutId);
        });
    },
  });
}