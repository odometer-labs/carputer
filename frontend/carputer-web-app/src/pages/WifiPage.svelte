<script>
  import { onDestroy, onMount } from "svelte";
  import BackButton from "../assets/components/BackButton.svelte";
  import SystemIndicators from "../assets/components/SystemIndicators.svelte";
  import WifiIndicator from "../assets/components/WifiIndicator.svelte";
  import {
    activateWifiConnection,
    createAndActivateWifiConnection,
    deactivateCurrentWifiConnection,
    getCurrentWifiConnection,
    getSavedWifiConnections,
    getWifiAccessPoints,
  } from "../api/wifiApi";
  import { setWifiConnected, setWifiDisconnected } from "../stores/wifiStore";

  let isWifiOn = false;
  let wifiStatus = "OFF";
  let isLoading = true;
  let errorMessage = "";
  let currentConnection = null;
  let savedConnections = [];
  let accessPoints = [];
  let busySsid = "";
  let networkScanIntervalId = null;
  let isNetworkScanInFlight = false;

  const NETWORK_SCAN_INTERVAL_MS = 10000;

  $: wifiStatus = isWifiOn ? "ON" : "OFF";
  $: {
    if (isWifiOn && currentConnection) {
      const ap = accessPoints.find((p) => p.ssid === currentConnection.ssid);
      setWifiConnected(currentConnection.ssid, ap?.signal_strength ?? 0);
    } else {
      setWifiDisconnected();
    }
  }
  $: otherNetworks = accessPoints
    .filter((accessPoint) => accessPoint.ssid)
    .filter((accessPoint) => accessPoint.ssid !== currentConnection?.ssid)
    .sort((a, b) => b.signal_strength - a.signal_strength);

  onMount(async () => {
    await loadInitialState();
  });

  onDestroy(() => {
    stopNetworkScanLoop();
  });

  async function loadInitialState() {
    try {
      isLoading = true;
      errorMessage = "";

      const [connection, saved, nearby] = await Promise.all([
        getCurrentWifiConnection(),
        getSavedWifiConnections(),
        getWifiAccessPoints(),
      ]);

      currentConnection = connection;
      savedConnections = saved;
      accessPoints = nearby;
      isWifiOn = connection !== null;
      if (isWifiOn) {
        startNetworkScanLoop();
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

    if (nextState) {
      // Turning ON: start scanning, keep toggle ON even if a scan fails
      isWifiOn = true;
      startNetworkScanLoop();
      try {
        const [connection, saved, nearby] = await Promise.all([
          getCurrentWifiConnection(),
          getSavedWifiConnections(),
          getWifiAccessPoints(),
        ]);
        currentConnection = connection;
        savedConnections = saved;
        accessPoints = nearby;
      } catch (error) {
        errorMessage = `Failed to scan Wi-Fi networks: ${String(error)}`;
      }
    } else {
      // Turning OFF: stop scanning and deactivate
      isWifiOn = false;
      stopNetworkScanLoop();
      currentConnection = null;
      accessPoints = [];
      try {
        await deactivateCurrentWifiConnection();
      } catch (error) {
        errorMessage = `Failed to deactivate Wi-Fi: ${String(error)}`;
      }
    }
  }

  async function refreshNearbyNetworks() {
    if (!isWifiOn || isNetworkScanInFlight) {
      return;
    }

    isNetworkScanInFlight = true;
    try {
      accessPoints = await getWifiAccessPoints();
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
        const password = window.prompt(`Enter password for ${accessPoint.ssid}`);
        if (!password) {
          busySsid = "";
          return;
        }

        await createAndActivateWifiConnection({
          hotspot: false,
          connection_id: accessPoint.ssid,
          ssid: accessPoint.ssid,
          password,
        });
      }

      const [connection, saved] = await Promise.all([
        getCurrentWifiConnection(),
        getSavedWifiConnections(),
      ]);
      currentConnection = connection;
      savedConnections = saved;
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
        checked={isWifiOn}
        onchange={handleWifiToggle}
      />
      
      <!-- Icon changes based on state -->
      <i class={isWifiOn ? "iconoir-switch-on" : "iconoir-switch-off"}></i>

    </label>

    <h3 class={isWifiOn ? "wifi_text_on" : "wifi_text_off"}>{wifiStatus}</h3>
  </div>


  <!-- this is just a box to tell the user that below
      is the current connection                       -->
  <div class="option-box">
    <h3>Currently Connected To:</h3>
  </div>

  <div class="network-box">
    {#if isLoading}
      <p class="network-message">Loading current connection...</p>
    {:else if currentConnection}
      <div class="network-row active-network">
        <span class="network-ssid">{currentConnection.ssid}</span>
        <span class="network-signal">Connected</span>
      </div>
    {:else}
      <p class="network-message">No active Wi-Fi connection.</p>
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
    {:else if otherNetworks.length === 0}
      <p class="network-message">No additional networks found.</p>
    {:else}
      {#each otherNetworks as accessPoint}
        <button
          class="network-row"
          type="button"
          onclick={() => connectToNetwork(accessPoint)}
          disabled={!isWifiOn || !!busySsid}
        >
          <span class="network-ssid">{accessPoint.ssid}</span>
          <span class="network-signal">
            {#if busySsid === accessPoint.ssid}
              Connecting...
            {:else}
              Signal: {accessPoint.signal_strength}%
            {/if}
          </span>
        </button>
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
