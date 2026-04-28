export interface LineString {
  type: "LineString";
  coordinates: [number, number][];
}

export interface Track {
  track_id: number;
  geom: LineString;
  start_time: string;
  end_time: string | null;
}

export interface DeleteTrackResponse {
  result: string;
}
