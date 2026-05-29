export const API_BASE = "/api/v1";

export const DEVICE_LOG_FILE_URL = "/device-logs/carputer-system.log";

export const ENDPOINTS = {
  listTracks: `${API_BASE}/tracks`,
  importTracks: `${API_BASE}/tracks/import`,
  importTracksGpx: `${API_BASE}/tracks/import/gpx`,
  exportTracksGpx: `${API_BASE}/tracks/export/gpx`,
  deleteTrack: `${API_BASE}/tracks`,
};
