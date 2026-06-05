import Feature from 'ol/Feature.js';
import LineString from 'ol/geom/LineString.js';
import VectorLayer from 'ol/layer/Vector.js';
import VectorSource from 'ol/source/Vector.js';
import { Style, Stroke } from 'ol/style.js';
import { fromLonLat } from 'ol/proj.js';

import type { Track } from '../../api/types';


export interface TrackLayers {
  oldTrackLayer: VectorLayer;
  oldTrackSource: VectorSource;

  currentTrackLayer: VectorLayer;
  currentTrackSource: VectorSource;
}

// set up the old tracks that the user has been on previously
export function renderTracks(
  source: VectorSource,
  tracks: Track[],
  selectedTrackId: number | null
): void {

  source.clear();

  tracks.forEach((track) => {
    const coords =
      track.geom.coordinates.map(([lon, lat]) =>
        fromLonLat([lon, lat])
      );

    const feature = new Feature({
      geometry: new LineString(coords),
      trackId: track.track_id
    });

    feature.set('isActive', track.track_id === selectedTrackId);

    source.addFeature(feature);
  });
}


export function createTrackLayers(
  getSelectedColor: (alpha?: number) => string,
  getRestingColor: (alpha?: number) => string,
  getTrackWidth: (offset?: number) => number
): TrackLayers {

  const oldTrackSource = new VectorSource();

  const oldTrackLayer = new VectorLayer({
    source: oldTrackSource,
    minZoom: 13,
    style: (feature) => {
      const isActive = feature.get('isActive');

      return new Style({
        stroke: new Stroke({
          color: isActive
            ? getSelectedColor(0.95)
            : getRestingColor(0.55),

          width: isActive
            ? getTrackWidth(1)
            : getTrackWidth(0)
        })
      });
    }
  });

  const currentTrackSource = new VectorSource();

  const currentTrackLayer = new VectorLayer({
    source: currentTrackSource,
    style: () =>
      new Style({
        stroke: new Stroke({
          color: getSelectedColor(0.8),
          width: getTrackWidth()
        })
      })
  });

  return {
    oldTrackLayer,
    oldTrackSource,
    currentTrackLayer,
    currentTrackSource
  };
}

