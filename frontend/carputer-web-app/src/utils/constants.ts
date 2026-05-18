export const API_BASE = "/api/v1";

export const ENDPOINTS = {
  startTrack: `${API_BASE}/tracks-start`,
  endTrack: `${API_BASE}/tracks-end`,
  listTracks: `${API_BASE}/tracks`,
  getTrack: `${API_BASE}/tracks`,
  updateTrack: `${API_BASE}/tracks`,
  deleteTrack: `${API_BASE}/tracks`,
  addTrackPoint: `${API_BASE}/tracks/point`,
  getLatestTrackPoint: `${API_BASE}/tracks-latest-point`,
  checkNewRoad: `${API_BASE}/tracks-check-new-road`,
  getCurrentPosition: "/ws/get-current-pos",
  getPositionStream: "/ws/get-position",
  sysHealthStream: "/ws/sys-health",
  getAprsStations: `${API_BASE}/aprs/stations`,
};
