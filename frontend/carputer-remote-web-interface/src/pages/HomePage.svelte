<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import {
    getLatestVersion,
    listTracks,
    subscribeToPositionStream,
    subscribeToSysHealth,
  } from '../api/restApi';
  import type { GPSData, SysHealthData } from '../api/types';
  import {
    deriveSystemHealthStatus,
    formatBytes,
    formatRate,
    formatUptime,
    UNAVAILABLE_LABEL,
  } from '../utils/homeHealth';

  let sysHealth: SysHealthData | null = null;
  let latestPosition: GPSData | null = null;
  let currentPatchLevel: string | null = null;
  let gpsTrackCount: number | null = null;
  let lastHealthUpdateAt: Date | null = null;
  let stopSysHealthSubscription: (() => void) | null = null;
  let stopPositionSubscription: (() => void) | null = null;
  let refreshTimer: ReturnType<typeof setInterval> | null = null;
  let healthStatus: string = UNAVAILABLE_LABEL;
  let cpuUsageText: string = UNAVAILABLE_LABEL;
  let memoryUsageText: string = UNAVAILABLE_LABEL;
  let diskFreeText: string = UNAVAILABLE_LABEL;
  let serviceUptimeText: string = UNAVAILABLE_LABEL;
  let loadAverageText: string = UNAVAILABLE_LABEL;
  let networkText: string = UNAVAILABLE_LABEL;
  let latestGpsFixText: string = UNAVAILABLE_LABEL;
  let patchLevelText: string = UNAVAILABLE_LABEL;
  let trackCountText: string = UNAVAILABLE_LABEL;
  let lastHealthUpdateText: string = 'Waiting for telemetry...';

  $: healthStatus = deriveSystemHealthStatus(sysHealth);
  $: cpuUsageText = sysHealth ? `${sysHealth.cpu.percent_total.toFixed(1)}%` : UNAVAILABLE_LABEL;
  $: memoryUsageText = sysHealth ? `${sysHealth.memory.used_percent.toFixed(1)}%` : UNAVAILABLE_LABEL;
  $: diskFreeText = sysHealth ? formatBytes(sysHealth.disk.free_bytes) : UNAVAILABLE_LABEL;
  $: serviceUptimeText = sysHealth ? formatUptime(sysHealth.uptime_seconds) : UNAVAILABLE_LABEL;
  $: loadAverageText = sysHealth
    ? `${sysHealth.cpu.load_avg_1.toFixed(2)} / ${sysHealth.cpu.load_avg_5.toFixed(2)} / ${sysHealth.cpu.load_avg_15.toFixed(2)}`
    : UNAVAILABLE_LABEL;
  $: networkText = sysHealth
    ? `Down ${formatRate(sysHealth.network.recv_rate_bytes)} | Up ${formatRate(sysHealth.network.send_rate_bytes)}`
    : UNAVAILABLE_LABEL;
  $: latestGpsFixText = latestPosition
    ? `${latestPosition.latitude.toFixed(5)}, ${latestPosition.longitude.toFixed(5)} | ${latestPosition.speed.toFixed(1)} m/s @ ${latestPosition.heading.toFixed(0)}°`
    : UNAVAILABLE_LABEL;
  $: patchLevelText = currentPatchLevel ?? UNAVAILABLE_LABEL;
  $: trackCountText = gpsTrackCount !== null ? `${gpsTrackCount}` : UNAVAILABLE_LABEL;
  $: lastHealthUpdateText = lastHealthUpdateAt ? lastHealthUpdateAt.toLocaleTimeString() : 'Waiting for telemetry...';

  async function loadDashboardSnapshot(): Promise<void> {
    const [trackResult, versionResult] = await Promise.allSettled([
      listTracks(),
      getLatestVersion(),
    ]);

    if (trackResult.status === 'fulfilled') {
      gpsTrackCount = Array.isArray(trackResult.value) ? trackResult.value.length : null;
    } else {
      gpsTrackCount = null;
      console.error('Failed to fetch track count:', trackResult.reason);
    }

    if (versionResult.status === 'fulfilled') {
      currentPatchLevel = versionResult.value;
    } else {
      currentPatchLevel = null;
      console.error('Failed to fetch current patch level:', versionResult.reason);
    }
  }

  onMount(() => {
    loadDashboardSnapshot();

    stopSysHealthSubscription = subscribeToSysHealth(
      (data) => {
        sysHealth = data;
        lastHealthUpdateAt = new Date();
      },
      (error) => {
        console.error('System health stream error:', error);
      },
    );

    stopPositionSubscription = subscribeToPositionStream(
      (position) => {
        latestPosition = position;
      },
      (error) => {
        console.error('Position stream error:', error);
      },
    );

    // Keep slower-changing dashboard stats fresh.
    refreshTimer = setInterval(() => {
      loadDashboardSnapshot();
    }, 60_000);
  });

  onDestroy(() => {
    stopSysHealthSubscription?.();
    stopSysHealthSubscription = null;

    stopPositionSubscription?.();
    stopPositionSubscription = null;

    if (refreshTimer !== null) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  });

  function goToManageData() : void {
    push("/ManageData");
  }

  function goToTracks() : void {
    push("/Tracks");
  }


</script>

<main class="home-shell">
  <header class="app-bar">
    <h2>Remote Dashboard</h2>
  </header>

  <section class="content-grid">
    <article class="panel">
      <h3>System Health</h3>
      <p>Health status: {healthStatus}</p>
      <p>Current patch level: {patchLevelText}</p>
      <p>Number of GPS tracks: {trackCountText}</p>
      <p>CPU usage: {cpuUsageText}</p>
      <p>Memory usage: {memoryUsageText}</p>
      <p>Disk free: {diskFreeText}</p>
      <p>Service uptime: {serviceUptimeText}</p>
      <p>Load avg (1/5/15m): {loadAverageText}</p>
      <p>Network throughput: {networkText}</p>
      <p>Current GPS fix: {latestGpsFixText}</p>
      <p>Last health update: {lastHealthUpdateText}</p>
    </article>

    <article class="panel">
      <h3>Quick Actions</h3>
      <div class="action-list">
        <button class="action-btn" type="button" onclick={goToTracks}>View Tracks</button>
        <button class="action-btn" type="button" onclick={goToManageData}>Manage Data</button>
      </div>
    </article>
  </section>
</main>

<style>
  .home-shell {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    background: var(--surface-color, #eeeeee);
    color: var(--text-color, #111111);
  }

  .app-bar {
    background-color: var(--primary-color, rgba(188, 188, 188, 0.9));
    border-top: 2px solid #000000;
    border-bottom: 2px solid #000000;
    text-align: center;
    color: #000000;
    min-height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 1rem;
  }

  .app-bar h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
  }

  h3 {
    margin: 0 0 0.6rem;
    font-size: 1.15rem;
  }

  .content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1rem;
    padding: 1.25rem;
  }

  .panel {
    background-color: var(--primary-color, rgba(188, 188, 188, 0.9));
    border: 1px solid #ffffff;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
    padding: 1rem;
  }

  .panel p {
    margin: 0.35rem 0;
  }

  .action-list {
    display: grid;
    gap: 0.55rem;
  }

  .action-btn {
    width: 100%;
    border: 1px solid #ffffff;
    border-radius: 6px;
    background-color: var(--secondary-color, rgb(225, 225, 225));
    color: #222222;
    padding: 0.6rem 0.8rem;
    text-align: left;
    cursor: pointer;
    font: inherit;
    transition: background-color 0.2s ease, box-shadow 0.2s ease;
  }

  .action-btn:hover {
    background-color: #f1f1f1;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  }
</style>