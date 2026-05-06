import { writable } from "svelte/store";

export interface WifiState {
  isConnected: boolean;
  /** Signal strength as a percentage (0–100). 0 when disconnected. */
  signalStrength: number;
  ssid: string | null;
}

const INITIAL_STATE: WifiState = {
  isConnected: false,
  signalStrength: 0,
  ssid: null,
};

export const wifiStore = writable<WifiState>(INITIAL_STATE);

export function setWifiConnected(ssid: string, signalStrength: number): void {
  wifiStore.set({ isConnected: true, signalStrength, ssid });
}

export function setWifiDisconnected(): void {
  wifiStore.set({ isConnected: false, signalStrength: 0, ssid: null });
}
