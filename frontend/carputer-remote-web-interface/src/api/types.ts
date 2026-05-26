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

export interface GPSData {
  latitude: number;
  longitude: number;
  heading: number;
  speed: number;
}

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

export interface LatestVersionResponse {
  body?: {
    id?: number;
    version?: {
      version_number?: string;
      git_hash?: string | null;
      release_date?: string | null;
    };
  };
}
