export const API_BASE = "/api/v1";
export const API_V2_BASE = "/v2";

export const ENDPOINTS = {
  listTracks: `${API_V2_BASE}/tracks/list-tracks`,
  importTracks: `${API_V2_BASE}/tracks/import-track`,
  importTracksGpx: `${API_BASE}/tracks/import/gpx`,   // no v2 equivalent yet
  exportTracksGpx: `${API_BASE}/tracks/export/gpx`,   // no v2 equivalent yet
  deleteTrack: `${API_V2_BASE}/tracks`,
  getLatestVersion: `${API_V2_BASE}/versioning/latest`,
  getPositionStream: "/ws/get-position",
  sysHealthStream: "/ws/sys-health",
};
