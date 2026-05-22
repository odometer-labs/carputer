export const API_BASE = "/api/v1"; // legacy Python API
const API_V2_BASE = "/v2"; // core Go API

export const ENDPOINTS = {
  startTrack: `${API_V2_BASE}/tracks`,
  endTrack: `${API_V2_BASE}/tracks`,
  listTracks: `${API_V2_BASE}/tracks/list-tracks`,
  getTrack: `${API_V2_BASE}/tracks`,
  updateTrack: `${API_V2_BASE}/tracks`,
  deleteTrack: `${API_V2_BASE}/tracks`,
  addTrackPoint: `${API_V2_BASE}/tracks/track-point`,
  getLatestTrackPoint: `${API_BASE}/tracks-latest-point`,
  checkNewRoad: `${API_V2_BASE}/tracks/check-new-road`,
  getCurrentPosition: `${API_BASE}/position`,
  getPositionStream: "/ws/get-position",
  sysHealthStream: "/ws/sys-health",
  getAprsStations: `${API_V2_BASE}/aprs/stations`,
  addTrack: `${API_V2_BASE}/tracks/import-track`,
};
