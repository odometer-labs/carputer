export interface WifiAccessPoint {
  ssid: string;
  signal_strength: number;
  security?: string | null;
}

export interface StaticNetworkSettings {
  ip: string;
  gateway: string | null;
  netmask: number;
}

export interface WifiConnectionSettings {
  hotspot: boolean;
  connection_id: string | null;
  ssid: string;
  uuid: string | null;
  static_config: StaticNetworkSettings | null;
}

interface CreateWifiConnectionRequest {
  hotspot: boolean;
  connection_id: string;
  ssid: string;
  password?: string;
  static_config?: StaticNetworkSettings | null;
}

const WIFI_ENDPOINTS = {
  currentConnection: "/wifi/connection",
  savedConnections: "/wifi/connection/saved",
  activateConnection: "/wifi/connection/activate",
  deactivateConnection: "/wifi/connection/deactivate",
  accessPoints: "/wifi/access-points",
};

function assertResponseOk(response: Response, message: string) {
  if (!response.ok) {
    throw new Error(message);
  }
}

export async function getCurrentWifiConnection(): Promise<WifiConnectionSettings | null> {
  const response = await fetch(WIFI_ENDPOINTS.currentConnection, {
    method: "GET",
  });

  assertResponseOk(response, "Failed to fetch current Wi-Fi connection");
  return response.json();
}

export async function getSavedWifiConnections(): Promise<
  WifiConnectionSettings[]
> {
  const response = await fetch(WIFI_ENDPOINTS.savedConnections, {
    method: "GET",
  });

  assertResponseOk(response, "Failed to fetch saved Wi-Fi connections");
  return response.json();
}

export async function getWifiAccessPoints(): Promise<WifiAccessPoint[]> {
  const response = await fetch(WIFI_ENDPOINTS.accessPoints, {
    method: "GET",
  });

  assertResponseOk(response, "Failed to fetch Wi-Fi access points");
  return response.json();
}

export async function activateWifiConnection(uuid: string): Promise<void> {
  const response = await fetch(
    `${WIFI_ENDPOINTS.activateConnection}?uuid=${encodeURIComponent(uuid)}`,
    {
      method: "PUT",
    },
  );

  assertResponseOk(response, "Failed to activate Wi-Fi connection");
}

export async function deactivateCurrentWifiConnection(): Promise<void> {
  const response = await fetch(WIFI_ENDPOINTS.deactivateConnection, {
    method: "PUT",
  });

  assertResponseOk(response, "Failed to deactivate Wi-Fi connection");
}

export async function createAndActivateWifiConnection(
  payload: CreateWifiConnectionRequest,
): Promise<void> {
  const response = await fetch(WIFI_ENDPOINTS.currentConnection, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  assertResponseOk(response, "Failed to create and activate Wi-Fi connection");
}
