export interface LineString {
  type: "LineString";
  coordinates: [number, number][];
}

export interface Track {
  track_id: number;
  geom: LineString;
  start_time: string;
  end_time: string | null;
  track_name?: string | null;
}

export interface DeleteTrackResponse {
  result: string;
}

export interface ImportTracksResponse {
  result?: string;
  status?: string;
  message?: string;
  track_id?: number;
}
