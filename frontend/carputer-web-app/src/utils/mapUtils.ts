import type { TrackRange } from "../services/settings_preferences";
import { getDistance as getGeoDistance } from 'ol/sphere.js';
import type { Track } from '../api/types';

// this page is dedicated to have function for the HomeMapPage to help reduce clutter


// this function gets the date by 1 day, week, month or year. 
// if there shouldn't be a date, if the user has selected all tracks
// to show then it should default to null
export function getAfterDate(range: TrackRange) : Date | null {
  if (range === "all") return null;

  const date = new Date();

  // set to midnight
  date.setHours(0, 0, 0, 0);

  switch (range) {
    case "day":
      date.setDate(date.getDate() - 1);
      break;
    case "week":
      date.setDate(date.getDate() - 7);
      break;
    case "month":
      date.setMonth(date.getMonth() - 1);
      break;
    case "year":
      date.setFullYear(date.getFullYear() - 1);
      break;
  }

  return date;
}


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
  const dx = a[0] - b[0];
  const dy = a[1] - b[1];
  return Math.sqrt(dx * dx + dy * dy);
}


export function bytesToGigabytes(bytes: number): number {
  return bytes / 1_073_741_824;
}