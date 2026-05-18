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
  end_time: string | null; //ISO format, also it can be null incase it is the current track.
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

// GPS payload returned by backend websocket /ws/get-position
export interface GPSData {
  latitude: number;
  longitude: number;
  heading: number;
  speed: number;
}

// System health payload from Go service /ws/sys-health
export interface SysHealthData {
  uptime_seconds: number;
  cpu: {
    percent_total: number;
    percent_per_core: number[];
    load_avg_1: number;
    load_avg_5: number;
    load_avg_15: number;
  };
  memory: {
    total_bytes: number;
    used_bytes: number;
    available_bytes: number;
    cached_bytes: number;
    free_bytes: number;
    used_percent: number;
  };
  disk: {
    total_bytes: number;
    used_bytes: number;
    free_bytes: number;
    used_percent: number;
  };
  network: {
    bytes_recv: number;
    bytes_sent: number;
    recv_rate_bytes: number;
    send_rate_bytes: number;
  };
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
