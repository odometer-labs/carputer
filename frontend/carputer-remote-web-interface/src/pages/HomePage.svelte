<script lang="ts">
  import { push } from 'svelte-spa-router';

  type SystemHealth = {
    systemHealthStatus: string;
    cpuUsagePercent: number;
    memoryUsagePercent: number;
    diskFreeGb: number;
    serviceUptime: string;
    currentPatchLevel: string;
    gpsTrackCount: number;
  };

  const systemHealth: SystemHealth = {
    systemHealthStatus: 'Healthy',
    cpuUsagePercent: 18,
    memoryUsagePercent: 42,
    diskFreeGb: 28.4,
    serviceUptime: '2d 06h',
    currentPatchLevel: '0.3.2',
    gpsTrackCount: 147
  };

  function goToLogs() : void {
    push("/Logs");
  }

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
      <p>Health status: {systemHealth.systemHealthStatus}</p>
      <p>Current patch level: {systemHealth.currentPatchLevel}</p>
      <p>Number of GPS tracks: {systemHealth.gpsTrackCount}</p>
      <p>CPU usage: {systemHealth.cpuUsagePercent}%</p>
      <p>Memory usage: {systemHealth.memoryUsagePercent}%</p>
      <p>Disk free: {systemHealth.diskFreeGb.toFixed(1)} GB</p>
      <p>Service uptime: {systemHealth.serviceUptime}</p>
    </article>

    <article class="panel">
      <h3>Quick Actions</h3>
      <div class="action-list">
        <button class="action-btn" type="button" onclick={goToLogs}>View Logs</button>
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