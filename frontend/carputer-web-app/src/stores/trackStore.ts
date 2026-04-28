import { writable, type Writable } from "svelte/store";
import { startTrack, endTrack, listTracks } from "../api/restApi";
import type { Track } from "../api/types"


export interface Tracks {
  isTracking: boolean;
  trackId: number | null;

  tracks: Track[];  // holds the tracks from backend.

  selectedTrackId: number | null;
}


class TrackStore {
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
    });
    
    //this is to make it into a store
    this.subscribe = this.store.subscribe;
  }

  //A function that calls the rest api startTrack and changes values from this class
  async start() {
    try {
      const res = await startTrack();

      this.store.update(state => ({
        ...state,
        isTracking: true,
        trackId: res.create_track
      }));
    } catch (error) {
      console.error(error);
    }
  }

  // a function that calls the rest api endTrack and changes the values isTracking 
  // to false and trackId to null
  async end() {
    try {
      await endTrack();

      this.store.update(state => ({
        ...state,
        isTracking: false,
        trackId: null
      }));
    } catch (error) {
      console.error(error);
    }
  }

  async loadTracks() {
    try {
      const tracks = await listTracks();

      this.store.update(state => ({
        ...state,
        tracks
      }));
    } catch (error) {
      console.error(error);
    }
  }

  //sets what track was selected.
  selectTrack(trackId: number) {
    this.store.update(state => ({
      ...state,
      selectedTrackId: state.selectedTrackId === trackId ? null : trackId
    }));
  }

  //this might be deleted later, for now it helps showcase tracks on the map
  setTrack(tracks: Track[]) {
    this.store.update(state => ({
      ...state, 
      tracks
    }));
  }
}

// used to access the stored values, singleton
export const trackStore = new TrackStore();
