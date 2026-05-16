<script>
  import { onDestroy, onMount } from "svelte";
  import BackButton from "../assets/components/BackButton.svelte";
  import SystemIndicators from "../assets/components/SystemIndicators.svelte";
  import WifiIndicator from "../assets/components/WifiIndicator.svelte";
  import wifi0 from "../assets/icons/wifi-signal0-bold.svg";
  import wifi1 from "../assets/icons/wifi-signal1-bold.svg";
  import wifi2 from "../assets/icons/wifi-signal2-bold.svg";
  import wifi3 from "../assets/icons/wifi-signal3-bold.svg";
  import lock_icon from "../assets/icons/lock-bold.svg";

  const wifiIcons = [wifi0, wifi1, wifi2, wifi3];

  function signalIcon(strength) {
    if (strength >= 67) return wifiIcons[3];
    if (strength >= 34) return wifiIcons[2];
    if (strength > 0)   return wifiIcons[1];
    return wifiIcons[0];
  }

  function dedupeAccessPointsBySsid(accessPointList) {
    const strongestBySsid = new Map();

    for (const accessPoint of accessPointList) {
      const ssid = String(accessPoint?.ssid ?? "").trim();
      if (!ssid) {
        continue;
      }

      const existing = strongestBySsid.get(ssid);
      if (!existing || accessPoint.signal_strength > existing.signal_strength) {
        strongestBySsid.set(ssid, { ...accessPoint, ssid });
      }
    }

    return Array.from(strongestBySsid.values());
  }

  function dedupeConnectionsBySsid(connectionList) {
    const uniqueBySsid = new Map();

    for (const connection of connectionList) {
      const ssid = String(connection?.ssid ?? "").trim();
      if (!ssid) {
        continue;
      }

      if (!uniqueBySsid.has(ssid)) {
        uniqueBySsid.set(ssid, { ...connection, ssid });
      }
    }

    return Array.from(uniqueBySsid.values());
  }

  import {
    activateWifiConnection,
    createAndActivateWifiConnection,
    deactivateCurrentWifiConnection,
    getCurrentWifiConnection,
    getSavedWifiConnections,
    getWifiAccessPoints,
  } from "../api/wifiApi";
  import { setWifiConnected, setWifiDisconnected, setWifiPower, wifiStore } from "../stores/wifiStore";

  let wifiStatus = "OFF";
  let isLoading = true;
  let errorMessage = "";
  let currentConnection = null;
  let savedConnections = [];
  let accessPoints = [];
  let busySsid = "";
  let selectedSsid = "";
  let selectedPassword = "";
  let networkScanIntervalId = null;
  let isNetworkScanInFlight = false;
  let hasMounted = false;

  const NETWORK_SCAN_INTERVAL_MS = 10000;
  const NETWORK_STARTUP_SCAN_ATTEMPTS = 5;
  const NETWORK_STARTUP_SCAN_DELAY_MS = 900;

  $: wifiStatus = $wifiStore.isWifiOn ? "ON" : "OFF";
  $: otherNetworks = dedupeAccessPointsBySsid(accessPoints)
    .filter((accessPoint) => accessPoint.ssid !== currentConnection?.ssid)
    .sort((a, b) => b.signal_strength - a.signal_strength);
  $: visibleOtherNetworks = otherNetworks;
  $: previousConnections = dedupeConnectionsBySsid(savedConnections)
    .filter((connection) => !connection.hotspot)
    .sort((a, b) => {
      if (a.ssid === currentConnection?.ssid) return -1;
      if (b.ssid === currentConnection?.ssid) return 1;
      return a.ssid.localeCompare(b.ssid);
    });
  $: selectedAccessPoint = visibleOtherNetworks.find((ap) => ap.ssid === selectedSsid) ?? null;
  $: selectedNetworkRequiresPassword = selectedAccessPoint
    ? isAccessPointSecured(selectedAccessPoint)
    : false;

  onMount(async () => {
    hasMounted = true;
    await loadInitialState();
  });

  onDestroy(() => {
    hasMounted = false;
    stopNetworkScanLoop();
  });

  function syncWifiStoreConnectionState() {
    if ($wifiStore.isWifiOn && currentConnection) {
      const ap = accessPoints.find((p) => p.ssid === currentConnection.ssid);
      setWifiConnected(currentConnection.ssid, ap?.signal_strength ?? 0);
      return;
    }

    setWifiDisconnected();
  }

  async function loadInitialState() {
    try {
      isLoading = true;
      errorMessage = "";

      const [connectionResult, savedResult, nearbyResult] = await Promise.allSettled([
        getCurrentWifiConnection(),
        getSavedWifiConnections(),
        getWifiAccessPoints(),
      ]);

      if (!hasMounted) {
        return;
      }

      if (connectionResult.status === "fulfilled") {
        currentConnection = connectionResult.value;
      }

      if (savedResult.status === "fulfilled") {
        savedConnections = savedResult.value;
      }

      if (nearbyResult.status === "fulfilled") {
        accessPoints = nearbyResult.value;
      }

      if (connectionResult.status === "fulfilled" && connectionResult.value) {
        setWifiPower(true);
      }

      syncWifiStoreConnectionState();

      if ($wifiStore.isWifiOn) {
        startNetworkScanLoop();
        await runStartupScanBurst();
      }

      const initialErrors = [];
      if (connectionResult.status === "rejected") {
        initialErrors.push("connection status");
      }
      if (savedResult.status === "rejected") {
        initialErrors.push("saved networks");
      }
      if (nearbyResult.status === "rejected") {
        initialErrors.push("nearby networks");
      }

      if (initialErrors.length > 0) {
        errorMessage = `Failed to load ${initialErrors.join(", ")}. Retrying in background.`;
      }
    } catch (error) {
      errorMessage = `Failed to load Wi-Fi status: ${String(error)}`;
    } finally {
      isLoading = false;
    }
  }

  async function handleWifiToggle(event) {
    const nextState = event.currentTarget.checked;
    errorMessage = "";
    setWifiPower(nextState);
    syncWifiStoreConnectionState();

    if (nextState) {
      // Turning ON: start scanning, keep toggle ON even if a scan fails
      startNetworkScanLoop();
      try {
        const [connection, saved] = await Promise.all([
          getCurrentWifiConnection(),
          getSavedWifiConnections(),
        ]);

        await runStartupScanBurst();

        currentConnection = connection;
        savedConnections = saved;
      } catch (error) {
        errorMessage = `Failed to scan Wi-Fi networks: ${String(error)}`;
      }
    } else {
      // Turning OFF: stop scanning and deactivate
      stopNetworkScanLoop();
      currentConnection = null;
      accessPoints = [];
      syncWifiStoreConnectionState();
      try {
        await deactivateCurrentWifiConnection();
      } catch (error) {
        errorMessage = `Failed to deactivate Wi-Fi: ${String(error)}`;
      }
    }
  }

  async function refreshNearbyNetworks() {
    if (!$wifiStore.isWifiOn || isNetworkScanInFlight) {
      return;
    }

    isNetworkScanInFlight = true;
    try {
      const [nearbyResult, connectionResult] = await Promise.allSettled([
        getWifiAccessPoints(),
        getCurrentWifiConnection(),
      ]);

      if (!hasMounted) {
        return;
      }

      if (nearbyResult.status === "fulfilled") {
        accessPoints = nearbyResult.value;
      }

      if (connectionResult.status === "fulfilled") {
        currentConnection = connectionResult.value;
      }

      syncWifiStoreConnectionState();

      if (nearbyResult.status === "rejected" && connectionResult.status === "rejected") {
        errorMessage = "Failed to refresh Wi-Fi status. Retrying...";
      } else {
        errorMessage = "";
      }
    } catch (error) {
      errorMessage = `Failed to scan nearby networks: ${String(error)}`;
    } finally {
      isNetworkScanInFlight = false;
    }
  }

  function startNetworkScanLoop() {
    if (networkScanIntervalId !== null) {
      return;
    }

    // Trigger one scan immediately so users don't wait for the first interval tick.
    void refreshNearbyNetworks();

    networkScanIntervalId = window.setInterval(() => {
      void refreshNearbyNetworks();
    }, NETWORK_SCAN_INTERVAL_MS);
  }

  function stopNetworkScanLoop() {
    if (networkScanIntervalId === null) {
      return;
    }

    window.clearInterval(networkScanIntervalId);
    networkScanIntervalId = null;
  }

  async function runStartupScanBurst() {
    for (let attempt = 0; attempt < NETWORK_STARTUP_SCAN_ATTEMPTS; attempt += 1) {
      await refreshNearbyNetworks();
      if (accessPoints.length > 0) {
        return;
      }

      await new Promise((resolve) => {
        window.setTimeout(resolve, NETWORK_STARTUP_SCAN_DELAY_MS);
      });
    }
  }

  function isAccessPointSecured(accessPoint) {
    const security = String(accessPoint?.security ?? "").trim().toLowerCase();
    if (!security) {
      return false;
    }
    return !["none", "open", "--"].includes(security);
  }

  function formatSecurity(accessPoint) {
    const security = String(accessPoint?.security ?? "").trim();
    if (!security || security.toLowerCase() === "open" || security.toLowerCase() === "none") {
      return "Open network";
    }
    return `Secured (${security})`;
  }

  function selectNetwork(accessPoint) {
    if (busySsid) {
      return;
    }

    if (selectedSsid === accessPoint.ssid) {
      selectedSsid = "";
      selectedPassword = "";
      return;
    }

    selectedSsid = accessPoint.ssid;
    selectedPassword = "";
    errorMessage = "";
  }

  function clearSelection() {
    selectedSsid = "";
    selectedPassword = "";
  }

  async function connectToNetwork(accessPoint) {
    busySsid = accessPoint.ssid;
    errorMessage = "";

    try {
      const existing = savedConnections.find(
        (connection) => connection.ssid === accessPoint.ssid && connection.uuid,
      );

      if (existing?.uuid) {
        await activateWifiConnection(existing.uuid);
      } else {
        const requiresPassword = isAccessPointSecured(accessPoint);
        if (requiresPassword && !selectedPassword.trim()) {
          errorMessage = `Password required for ${accessPoint.ssid}.`;
          return;
        }

        await createAndActivateWifiConnection({
          hotspot: false,
          connection_id: accessPoint.ssid,
          ssid: accessPoint.ssid,
          ...(requiresPassword ? { password: selectedPassword.trim() } : {}),
        });
      }

      const [connection, saved] = await Promise.all([
        getCurrentWifiConnection(),
        getSavedWifiConnections(),
      ]);
      currentConnection = connection;
      savedConnections = saved;
      syncWifiStoreConnectionState();
      clearSelection();
    } catch (error) {
      errorMessage = `Failed to connect to ${accessPoint.ssid}: ${String(error)}`;
    } finally {
      busySsid = "";
    }
  }
</script>


<div class="translucent-overlay">



  
  <div class="title-box">
    <!-- this is the exit buttion -->
    <BackButton />
    <h2>Wifi</h2>

    <SystemIndicators 
      isActiveBackground={false} 
      isWifiActive={false} 
      isRoadDiscoverActive={false}
    />
  </div>

  <!-- This button is to disable the wifi -->
  <div class="switch-box">
    <!-- this is the wifi indicator encased in a span so that I can style it.-->
    <span style="transform: scale(1.3); position:relative; top:-6px;"><WifiIndicator /></span>

    <label class="switch">
      <input
        type="checkbox"
        checked={$wifiStore.isWifiOn}
        onchange={handleWifiToggle}
      />
      
      <!-- Icon changes based on state -->
      <i class={$wifiStore.isWifiOn ? "iconoir-switch-on" : "iconoir-switch-off"}></i>

    </label>

    <h3 class={$wifiStore.isWifiOn ? "wifi_text_on" : "wifi_text_off"}>{wifiStatus}</h3>
  </div>


  <!-- this is just a box to tell the user that below
      is the current connection                       -->
  <div class="option-box connected-to-box">
    <h3>Connected To:</h3>
    <h3 class="connected-to-name">{currentConnection?.ssid ?? "None"}</h3>
  </div>

  <div class="option-box">
    <h3>Previously Connected To:</h3>
  </div>
  
  <div class="network-box">
    {#if isLoading}
      <p class="network-message">Loading current connection...</p>
    {:else if previousConnections.length > 0}
      {#each previousConnections as connection}
        <div class="network-row {connection.ssid === currentConnection?.ssid ? 'active-network' : ''}">
          <span class="network-ssid">{connection.ssid}</span>
          <span class="network-signal">
            {connection.ssid === currentConnection?.ssid ? "Connected" : "Saved"}
          </span>
        </div>
      {/each}
    {:else}
      <p class="network-message">No previously connected Wi-Fi networks.</p>
    {/if}
  </div>
  
  <!-- this is just a box to tell the user that below
      is the aviable connections                    -->
  <div class="option-box" style="margin-top: 10%;">
    <h3>Other Networks:</h3>
  </div>

  <div class="network-box">
    {#if isLoading}
      <p class="network-message">Scanning for nearby networks...</p>
    {:else if visibleOtherNetworks.length === 0}
      <p class="network-message">No additional networks found.</p>
    {:else}
      {#each visibleOtherNetworks as accessPoint}
        <div class="network-card {selectedSsid === accessPoint.ssid ? 'selected' : ''}">
          <button
            class="network-row"
            type="button"
            onclick={() => selectNetwork(accessPoint)}
            disabled={!$wifiStore.isWifiOn || !!busySsid}
            aria-expanded={selectedSsid === accessPoint.ssid}
          >
            <span class="network-ssid">{accessPoint.ssid}</span>
            <span class="network-signal">
              {#if isAccessPointSecured(accessPoint)}
                <!-- <i class="iconoir-lock network-lock-icon" aria-hidden="true"></i> -->
                 <img src={lock_icon} alt="Locked" style="width:22px; height:22px;" />
              {/if}
              {#if busySsid === accessPoint.ssid}
                Connecting...
              {:else}
                <img src={signalIcon(accessPoint.signal_strength)} alt="signal {accessPoint.signal_strength}%" style="width:22px; height:22px;" />
              {/if}
            </span>
          </button>

          {#if selectedSsid === accessPoint.ssid}
            <div class="network-details">
              <p class="network-security">{formatSecurity(accessPoint)}</p>

              {#if selectedNetworkRequiresPassword}
                <label class="password-input-wrap">
                  <input
                    type="password"
                    bind:value={selectedPassword}
                    placeholder="Enter Wi-Fi password"
                    disabled={!!busySsid}
                  />
                </label>
              {/if}

              <button
                class="connect-btn"
                type="button"
                onclick={() => connectToNetwork(accessPoint)}
                disabled={!$wifiStore.isWifiOn || !!busySsid}
              >
                {busySsid === accessPoint.ssid ? "Connecting..." : "Connect"}
              </button>
            </div>
          {/if}
        </div>
      {/each}
    {/if}
  </div>

</div>


<style>
  .option-box {
    display: flex;
    border-bottom: 1px solid rgba(0, 0, 0, 0.5);
    padding-left: 5%;
    padding-right: 5%;
    color: black;
  }

  .connected-to-box {
    justify-content: space-between;
    align-items: center;
  }

  .connected-to-name {
    margin-left: 12px;
    max-width: 50%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: right;
  }

  .network-box {
    padding: 1% 5%;
  }

  .network-row {
    width: 100%;
    border: 0;
    background: rgba(255, 255, 255, 0.55);
    border-radius: 12px;
    margin-top: 10px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #111;
    text-align: left;
  }

  .network-card {
    margin-top: 10px;
    border-radius: 12px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.35);
  }

  .network-card.selected {
    border: 1px solid rgba(33, 140, 0, 0.35);
  }

  .network-details {
    padding: 0 14px 12px;
    display: grid;
    gap: 8px;
  }

  .network-security {
    margin: 0;
    color: #1d1d1d;
    font-size: 0.85rem;
  }

  .password-input-wrap {
    display: grid;
    gap: 4px;
    font-size: 0.85rem;
    color: #222;
  }

  .password-input-wrap input {
    border: 1px solid rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 8px 10px;
    background: rgba(255, 255, 255, 0.8);
  }

  .connect-btn {
    border: 0;
    border-radius: 8px;
    background: rgba(33, 140, 0, 0.9);
    color: white;
    padding: 8px 10px;
    font-weight: 600;
    cursor: pointer;
  }

  .connect-btn:disabled {
    opacity: 0.6;
    cursor: default;
  }

  .network-row:disabled {
    opacity: 0.6;
  }

  .active-network {
    border: 1px solid rgba(33, 140, 0, 0.5);
    background: rgba(126, 201, 104, 0.2);
  }

  .network-ssid {
    font-weight: 700;
    max-width: 70%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .network-signal {
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .network-message {
    color: #222;
    margin-top: 12px;
  }

  .wifi_text_on {
    color: rgb(33, 140, 0);
    font-size: 18px;
    margin-left: 5%;
    width: 50px;
  }
  .wifi_text_off {
    color: rgb(180, 42, 0);
    font-size: 18px;
    margin-left: 5%;
    width: 50px;
  } 
  .switch {
    cursor: pointer;
    color: #333;

    display: inline-block;

    user-select: none; /* this to make it so the users can't highlight it or the surounding images */
    -webkit-user-select: none;
  }

  .switch input {
    display: none; 
  }

  .switch i {
    font-size: 64px;
    display: inline-block;
    cursor: pointer;
  }

  .switch-box {
    position: absolute;
    top: 1%;
    right: 1%;
    display: flex;
    align-items: center;
    justify-content: center;

    gap: 10px; /* controls how close they are */
  }
    
</style>
