<script lang="ts">
  import AppBar from '../assets/components/AppBar.svelte';
  import { parseSystemLog, type LogEntry, type LogSeverity } from '../utils/logs';

  const SAMPLE_LOG_FILE = [
    '2026-04-28 18:31:00,101 - handlers.py:12 - INFO: Logger initialized',
    '2026-04-28 18:32:00,101 - track_client.py:44 - WARNING: GPS signal degraded near tunnel entrance',
    '2026-04-28 18:33:00,101 - main.py:19 - ERROR: Failed to write point to local store',
    '2026-04-28 18:34:00,101 - main.py:30 - INFO: Retrying point upload in 10 seconds',
    '2026-04-28 18:35:00,101 - gpsd.py:8 - WARNING: GPS fix dropped below 4 satellites'
  ].join('\n');

  const severityOptions: Array<{ value: LogSeverity; label: string }> = [
    { value: 'error', label: 'Errors' },
    { value: 'warning', label: 'Warnings' },
    { value: 'message', label: 'Messages' }
  ];

  let parsedLogs = parseSystemLog(SAMPLE_LOG_FILE);
  let selectedSeverities: LogSeverity[] = ['error', 'warning', 'message'];
  let lastLoadedAt = new Date().toLocaleString();

  $: logsBySeverity = {
    error: parsedLogs.errors,
    warning: parsedLogs.warnings,
    message: parsedLogs.messages
  } satisfies Record<LogSeverity, LogEntry[]>;

  function formatEntryLabel(entry: LogEntry): string {
    return `${entry.timestamp} | ${entry.source} | ${entry.level}`;
  }

  function refreshLogs(): void {
    parsedLogs = parseSystemLog(SAMPLE_LOG_FILE);
    lastLoadedAt = new Date().toLocaleString();
  }

  function toggleSeverity(severity: LogSeverity): void {
    if (selectedSeverities.includes(severity)) {
      if (selectedSeverities.length === 1) {
        return;
      }

      selectedSeverities = selectedSeverities.filter((value) => value !== severity);
      return;
    }

    selectedSeverities = [...selectedSeverities, severity];
  }

  function getEntryOrder(entry: LogEntry): number {
    const [indexText] = entry.id.split('-', 1);
    return Number.parseInt(indexText ?? '-1', 10);
  }

  $: visibleEntries = selectedSeverities
    .flatMap((severity) => logsBySeverity[severity])
    .sort((left, right) => getEntryOrder(right) - getEntryOrder(left));
</script>

<main class="logs-shell">
  <AppBar title="Logs" />

  <section class="logs-content">
    <article class="panel overview-panel">
      <div>
        <h2>Device Log Viewer</h2>
        <p>
          This UI currently uses sample log data while the Pi log file contract is being finalized.
        </p>
      </div>

      <div class="overview-actions">
        <button class="refresh-btn" type="button" onclick={refreshLogs}>Refresh logs</button>
        <p>Total sample entries: {parsedLogs.total}</p>
        <p>Visible entries: {visibleEntries.length}</p>
        <p>Last loaded: {lastLoadedAt}</p>
      </div>
    </article>

    <article class="panel log-panel">
      <div class="panel-heading panel-heading-stack">
        <div>
          <h3>System Log Entries</h3>
          <p class="panel-subtitle">Choose which message types should appear in the list.</p>
        </div>

        <div class="filter-group" aria-label="Filter log severities">
          {#each severityOptions as option}
            <button
              class:selected={selectedSeverities.includes(option.value)}
              class:errors={option.value === 'error'}
              class:warnings={option.value === 'warning'}
              class:messages={option.value === 'message'}
              class="filter-chip"
              type="button"
              aria-pressed={selectedSeverities.includes(option.value)}
              onclick={() => toggleSeverity(option.value)}
            >
              {option.label}
            </button>
          {/each}
        </div>
      </div>

      {#if visibleEntries.length === 0}
        <p class="empty-state">Select at least one message type to display log entries.</p>
      {:else}
        <div class="entry-list">
          {#each visibleEntries as entry (entry.id)}
            <section class="log-entry" class:errors={entry.severity === 'error'} class:warnings={entry.severity === 'warning'} class:messages={entry.severity === 'message'}>
              <div class="entry-header">
                <p class="entry-meta">{formatEntryLabel(entry)}</p>
                <span class="severity-badge">{entry.severity}</span>
              </div>
              <p class="entry-message">{entry.message}</p>
            </section>
          {/each}
        </div>
      {/if}
    </article>
  </section>
</main>

<style>
  .logs-shell {
    width: 100%;
    min-height: 100%;
    background: var(--surface-color, #eeeeee);
    color: var(--text-color, #111111);
  }

  .logs-content {
    display: grid;
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

  .overview-panel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .overview-panel h2,
  .panel-heading h3 {
    margin: 0 0 0.5rem;
  }

  .overview-panel p,
  .panel-subtitle,
  .entry-message,
  .entry-meta {
    margin: 0;
  }

  .overview-actions {
    display: grid;
    gap: 0.5rem;
    min-width: 220px;
    align-content: start;
  }

  .refresh-btn {
    width: fit-content;
    border: 1px solid rgba(17, 17, 17, 0.18);
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.8);
    color: inherit;
    padding: 0.65rem 0.85rem;
    cursor: pointer;
    font: inherit;
    transition: background-color 120ms ease, transform 120ms ease;
  }

  .refresh-btn:hover {
    background: rgba(255, 255, 255, 0.96);
    transform: translateY(-1px);
  }

  .hint {
    margin-top: 0.75rem;
    font-size: 0.95rem;
  }

  .log-panel {
    min-height: 420px;
  }

  .panel-heading-stack {
    align-items: start;
    gap: 1rem;
  }

  .panel-subtitle {
    opacity: 0.78;
  }

  .panel-heading {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 0.85rem;
  }

  .filter-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .filter-chip {
    border: 1px solid rgba(17, 17, 17, 0.18);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.45);
    color: inherit;
    padding: 0.45rem 0.8rem;
    cursor: pointer;
    font: inherit;
    transition: background-color 120ms ease, border-color 120ms ease, transform 120ms ease;
  }

  .filter-chip.selected {
    background: rgba(255, 255, 255, 0.92);
    border-color: rgba(17, 17, 17, 0.4);
    transform: translateY(-1px);
  }

  .entry-list {
    display: grid;
    gap: 0.75rem;
    max-height: 62vh;
    overflow-y: auto;
    padding-right: 0.25rem;
  }

  .log-entry {
    display: grid;
    gap: 0.35rem;
    border-left: 4px solid rgba(0, 0, 0, 0.35);
    background: rgba(255, 255, 255, 0.48);
    border-radius: 6px;
    padding: 0.75rem;
  }

  .entry-header {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 0.75rem;
  }

  .severity-badge {
    min-width: 5.5rem;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.72);
    text-align: center;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: capitalize;
  }

  .log-entry.errors,
  .filter-chip.errors.selected {
    border-left-color: #a21d2b;
    border-color: #a21d2b;
  }

  .log-entry.warnings,
  .filter-chip.warnings.selected {
    border-left-color: #c07b00;
    border-color: #c07b00;
  }

  .log-entry.messages,
  .filter-chip.messages.selected {
    border-left-color: #146c8f;
    border-color: #146c8f;
  }

  .log-entry.errors .severity-badge {
    background: rgba(162, 29, 43, 0.14);
    color: #7a1220;
  }

  .log-entry.warnings .severity-badge {
    background: rgba(192, 123, 0, 0.16);
    color: #7a4d00;
  }

  .log-entry.messages .severity-badge {
    background: rgba(20, 108, 143, 0.14);
    color: #0d4c65;
  }

  .entry-meta {
    font-size: 0.82rem;
    opacity: 0.82;
  }

  .entry-message {
    line-height: 1.4;
    word-break: break-word;
  }

  .empty-state {
    opacity: 0.75;
  }

  @media (max-width: 700px) {
    .logs-content {
      padding: 1rem;
    }

    .entry-header,
    .panel-heading {
      flex-direction: column;
      align-items: stretch;
    }

    .entry-list {
      max-height: none;
    }
  }
</style>