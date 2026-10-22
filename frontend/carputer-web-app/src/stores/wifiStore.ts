import { writable } from "svelte/store";

export interface WifiState {
  isWifiOn: boolean;
  isConnected: boolean;
  /** Signal strength as a percentage (0–100). 0 when disconnected. */
  signalStrength: number;
  ssid: string | null;
}

const INITIAL_STATE: WifiState = {
  isWifiOn: true,
  isConnected: false,
  signalStrength: 0,
  ssid: null,
};

export const wifiStore = writable<WifiState>(INITIAL_STATE);

export function setWifiPower(isWifiOn: boolean): void {
  wifiStore.update((state) => ({ ...state, isWifiOn }));
}

export function setWifiConnected(ssid: string, signalStrength: number): void {
  wifiStore.update((state) => ({
    ...state,
    isConnected: true,
    signalStrength,
    ssid,
  }));
}

export function setWifiDisconnected(): void {
  wifiStore.update((state) => ({
    ...state,
    isConnected: false,
    signalStrength: 0,
    ssid: null,
  }));
}
