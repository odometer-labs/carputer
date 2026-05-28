import { writable, type Writable } from "svelte/store";
import {
  listTracks,
  checkNewRoad,
  addTrackPoint,
  importTrack,
  updateTrack,
} from "../api/restApi";
import type {
  Track,
  TrackPoint,
  LineString,
  UpdateTrackVal,
} from "../api/types";
import { reportNonVitalError } from "./errorStore";

export interface Tracks {
  isTracking: boolean;
  trackId: number | null;

  tracks: Track[]; // holds the tracks from backend.
  selectedTrackId: number | null;

  isOnNewRoad: boolean;
}

export class TrackStore {
  //this sets the store in the class and makes sure it can't be accessed inside
  private store: Writable<Tracks>;
  subscribe: Writable<Tracks>["subscribe"];

  //constructor, sets the defualt values
  constructor() {
    this.store = writable<Tracks>({
      isTracking: false,
      trackId: null,

      tracks: [],
      selectedTrackId: null,
      isOnNewRoad: false,
    });

    //this is to make it into a store
    this.subscribe = this.store.subscribe;
  }

  //A function that calls the rest api startTrack and changes values from this class
  async start() {
    try {
      //TODO: uncomment this once we have the API add track point working
      //const res = await startTrack();

      this.store.update((state) => ({
        ...state,
        isTracking: true,
        trackId: null, //TODO: change it to (trackId: res.id) once add track point works
      }));
    } catch (error) {
      reportNonVitalError(error, "trackStore.start", true);
    }
  }

  // a function that calls the rest api endTrack and changes the values isTracking
  // to false and trackId to null
  async end() {
    try {
      //TODO: uncomment this once we have the API add track point working
      //await endTrack();

      this.store.update((state) => ({
        ...state,
        isTracking: false,
        trackId: null,
      }));
    } catch (error) {
      reportNonVitalError(error, "trackStore.end", true);
    }
  }

  // adds a track point to the currently active track
  async addPoint(point: TrackPoint) {
    try {
      let currentTrackId: number | null = null;

      //get the current trackID from the store
      this.store.update((state) => {
        currentTrackId = state.trackId;
        return state;
      });

      //check if there is currently an active track
      if (currentTrackId == null) {
        throw new Error("No active tracks currently");
      }

      // send the point to backend
      await addTrackPoint(point);
    } catch (error) {
      reportNonVitalError(error, "trackStore.addPoint");
    }
  }

  async loadTracks() {
    try {
      const tracks = await listTracks();

      //this prevents unfinished tracks from being shown up on the map.
      const finishedTracks = tracks.filter((track) => track.end_time != null);

      this.store.update((state) => ({
        ...state,
        tracks: finishedTracks,
      }));
    } catch (error) {
      reportNonVitalError(error, "trackStore.loadTracks");
    }
  }

  //sets what track was selected.
  selectTrack(trackId: number) {
    this.store.update((state) => ({
      ...state,
      selectedTrackId: state.selectedTrackId === trackId ? null : trackId,
    }));
  }

  //exports a whole track to backend.
  async addTrack(line: LineString): Promise<number | null> {
    try {
      const res = await importTrack(line);

      return res.id;
    } catch (error) {
      reportNonVitalError(error, "trackStore.addTrack");
      return null;
    }
  }

  //this is used to update the track in the database
  async updateTrack(id: number, trackVal: UpdateTrackVal) {
    try {
      await updateTrack(id, trackVal);
    } catch (error) {
      reportNonVitalError(error, "trackStore.updateTrack");
    }
  }

  //checks if the current road has been driven on in the past
  async checkIfNewRoad() {
    try {
      const res = await checkNewRoad();

      this.store.update((state) => ({
        ...state,
        isOnNewRoad: res.is_new_road,
      }));
    } catch (error) {
      reportNonVitalError(error, "trackStore.checkIfNewRoad");
    }
  }
}

// used to access the stored values, singleton
export const trackStore = new TrackStore();
