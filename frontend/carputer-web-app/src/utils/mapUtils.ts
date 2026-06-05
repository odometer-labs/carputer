import { getDistance as getGeoDistance } from 'ol/sphere.js';
import type { Track } from '../api/types';
import { getDistance } from "ol/sphere";
import { toLonLat } from "ol/proj";

// this page is dedicated to have function for the HomeMapPage to help reduce clutter


export function isTrackWithinRadius(track: Track, centerLonLat: [number, number], radiusMeters: number): boolean {
  if (!track.geom?.coordinates?.length) {
    return false;
  }

  for (const [lon, lat] of track.geom.coordinates) {
    const distanceMeters = getGeoDistance(centerLonLat, [lon, lat]);
    if (distanceMeters <= radiusMeters) {
      return true;
    }
  }

  return false;
}


export function hexToRgba(hex: string, alpha: number): string {
  const normalized = hex.trim().replace("#", "");

  if (!/^[0-9a-fA-F]{6}$/.test(normalized)) {
    return `rgba(255, 52, 241, ${alpha})`;
  }

  const red = parseInt(normalized.slice(0, 2), 16);
  const green = parseInt(normalized.slice(2, 4), 16);
  const blue = parseInt(normalized.slice(4, 6), 16);

  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}


export function getDistanceMeters(a: [number, number], b: [number, number]): number {
  return getDistance(
    toLonLat(a),
    toLonLat(b)
  )
}