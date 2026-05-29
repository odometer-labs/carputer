export const API_BASE = "/api/v1";
export const API_V2_BASE = "/v2";

export const ENDPOINTS = {
  listTracks: `${API_BASE}/tracks`,
  importTracks: `${API_BASE}/tracks/import`,
  importTracksGpx: `${API_BASE}/tracks/import/gpx`,
  exportTracksGpx: `${API_BASE}/tracks/export/gpx`,
  deleteTrack: `${API_BASE}/tracks`,
  getLatestVersion: `${API_V2_BASE}/versioning/latest`,
  getPositionStream: "/ws/get-position",
  sysHealthStream: "/ws/sys-health",
};
