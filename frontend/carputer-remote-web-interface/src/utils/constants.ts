export const API_BASE = "/api/v1";
export const API_V2_BASE = "/v2";

export const DEVICE_LOG_FILE_URL = "/device-logs/carputer-system.log";

export const ENDPOINTS = {
  listTracks: `${API_BASE}/tracks`,
  deleteTrack: `${API_BASE}/tracks`,
  getLatestVersion: `${API_V2_BASE}/versioning/latest`,
  getPositionStream: "/ws/get-position",
  sysHealthStream: "/ws/sys-health",
};
