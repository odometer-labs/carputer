import { writable, type Writable } from "svelte/store";
import { startTrack, endTrack } from "../api/restApi";


export interface Tracks {
  isTracking: boolean;
  trackId: number | null;
}


class TrackStore {
  //this sets the store in the class and makes sure it can't be accessed inside
  private store: Writable<Tracks>;
  subscribe: Writable<Tracks>["subscribe"];

  //constructor, sets the defualt values
  constructor() {
    this.store = writable<Tracks>({
      isTracking: false,
      trackId: null
    });
    
    //this is to make it into a store
    this.subscribe = this.store.subscribe;
  }

  //A function that calls the rest api startTrack and changes values from this class
  async start() {
    try {
      const res = await startTrack();

      this.store.set({
        isTracking: true,
        trackId: res.createdTrackId
      });
    } catch (error) {
      console.error(error)
    }
  }

  // a function that calls the rest api endTrack and changes the values isTracking 
  // to false and trackId to null
  async end() {
    try {
      await endTrack();

      this.store.set({
        isTracking: false,
        trackId: null
      });
    } catch (error) {
      console.error(error)
    }
  }
}

// used to access the stored values, singleton
export const trackStore = new TrackStore();
