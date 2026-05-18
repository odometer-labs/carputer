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

export interface ImportTrackResponse {
  track_id: number;
  status: string;
}

export interface LineString {
  type: "LineString";
  coordinates: [number, number][];
}

export interface Track {
  track_id: number;
  geom: LineString;
  start_time: string; //ISO format
  end_time: string | null; //ISO format, also it can be null incase it is the current track.
  track_name: string | null;
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
  geom: string; // strangely this isn't in geojson but a string? might have to ask backend to change this
  speed_mph: number;
  heading_deg: number;
}

//this is used when updating a track
export interface UpdateTrackVal {
  start_time: string;
  end_time: string | null;
  track_name: string | null;
}

// GPS payload returned by backend websocket /ws/get-position
export interface GPSData {
  latitude: number;
  longitude: number;
  heading: number;
  speed: number;
}

export interface APRSStation {
  callsign: string;
  symbol_table: string;
  symbol_code: string;
  last_comment: string | null;
  last_seen: string; // ISO format datetime
  latitude: number;
  longitude: number;
  distance_m: number | null;
  packet_count: number;
}
