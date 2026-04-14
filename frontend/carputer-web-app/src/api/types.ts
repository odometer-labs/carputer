/*
    this file contains data types for the fastapi to use.
*/

export interface StartTrackResponse {
  create_track: number;
}

export interface EndTrackResponse {
  result: string;
}

export interface UpdateTrackResponse {
  result: string;
}

export interface DeleteTrackResponse {
  result: string;
}

export interface AddTrackPointResponse {
  result: string;
}

export interface CheckNewRoadResponse {
  is_new_road: boolean;
}

export interface LineString {
  type: "LineString";
  coordinates: [number, number][];
}

export interface Track {
  track_id: number;
  geom: LineString;
  start_time: string; //ISO format
  end_time: string | null;  //ISO format, also it can be null incase it is the current track.
}

// this if for addding a point on the track, used with the addTrackPoint api call
export interface TrackPoint {
  latitude: number;
  longitude: number;
  speed: number;
  heading: number;
}

// this is getting a track point from the get latest track point.
export interface LatestTrackPoint {
  point_id: number; // this is track point
  track_id: number;
  time_stamp: string;
  geom: string;        // strangely this isn't in geojson but a string? might have to ask backend to change this
  speed_mph: number;
  heading_deg: number;
}