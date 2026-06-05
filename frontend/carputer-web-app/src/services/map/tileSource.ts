import OSM from 'ol/source/OSM.js';
import ImageTile from 'ol/ImageTile.js';
import { ENDPOINTS } from '../../utils/constants';

//const for tileSource
const TRANSPARENT_TILE_DATA_URL = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==';
const TILE_FETCH_TIMEOUT_MS = 10000;

function getTileServerBaseUrl(): string {
  // In Vite dev (:5173), connect directly to the tile server on port 8070
  // In Docker (:3000), use the current origin
  if (window.location.port === "5173") {
    return `${window.location.protocol}//${window.location.hostname}:8070`;
  }

  return window.location.origin;
}

export function createBaseTileSource(useOnlineTiles: boolean): OSM {
  if (useOnlineTiles) {
    return new OSM();
  }

  return new OSM({
    url: `${getTileServerBaseUrl()}${ENDPOINTS.tileServer}`,
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