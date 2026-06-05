import aprsIconUrl from '../../assets/icons/aprs-bold.svg';
import { 
  Style,
  Circle, 
  Fill, 
  Stroke, 
  RegularShape, 
  Text,
  Icon,
} from 'ol/style.js';
import Feature from 'ol/Feature.js';
import Point from 'ol/geom/Point.js';
import { fromLonLat } from 'ol/proj.js';
import VectorLayer from 'ol/layer/Vector.js';
import VectorSource from 'ol/source/Vector.js';
import Cluster from 'ol/source/Cluster.js';


export interface AprsLayerObjects {
  layer: VectorLayer;
  source: VectorSource;
  cluster: Cluster
}

// TODO: there are appearently many different kinds of aprs icons so it may need
// to be able to shift through different icons for the situation. or if we decided
// to not implement different icons for different aprs then that fine, just remove
// this comment.
export function getAprsIcon(): string {
  return aprsIconUrl;
}


// this is the style for the pins, you can insert the image to the pin
export function getAprsPinStyle(img: string, isSelected: boolean = false): Style[] {
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


/**
 * Sets up feature points for APRS stations fetched from the backend API.
 */
export function addAprsPoint(
  source: VectorSource,
  lat: number,
  long: number,
  callsign: string,
  comment: string | null
): void {
  const aprsId = `${callsign}-${lat.toFixed(6)}-${long.toFixed(6)}`;

  const aprsMarker = new Feature({
    geometry: new Point(fromLonLat([long, lat])),
    aprsId,
    callsign,
    comment,
  });

  source.addFeature(aprsMarker);
}


export function createAprsLayer(
  getSelectedAprsId: () => string | undefined
): AprsLayerObjects {

  const source = new VectorSource();

  const cluster = new Cluster({
    distance: 30,
    source
  });

  const layer = new VectorLayer({
    source: cluster,
    minZoom: 0,
    style: (feature) => {
      const clusteredFeatures =
        feature.get('features') as Feature[] | undefined;

      if (!clusteredFeatures) {
        return undefined;
      }

      const size = clusteredFeatures.length;

      if (size === 1) {
        const inner = feature.get('features')[0] as Feature | undefined;

        const aprsId = inner?.get('aprsId') as string | undefined;

        const isSelected =
          aprsId !== undefined &&
          getSelectedAprsId() === aprsId;

        return getAprsPinStyle(getAprsIcon(), isSelected);
      }

      return new Style({
        image: new Circle({
          radius: 12,
          fill: new Fill({ color: '#3399CC' }),
          stroke: new Stroke({
            color: '#fff',
            width: 2
          })
        }),
        text: new Text({
          text: size.toString(),
          fill: new Fill({ color: '#fff' })
        })
      });
    }
  });

  return {
    layer,
    source,
    cluster
  };
}