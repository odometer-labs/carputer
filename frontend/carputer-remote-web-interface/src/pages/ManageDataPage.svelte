<script lang="ts">
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import AppBar from '../assets/components/AppBar.svelte';
  import { exportTracksGpx, importTracksGeoJson, importTracksGpx } from '../api/restApi';
  import {
    clearExportQueue,
    exportTrackCount,
    exportTrackIds,
    exportTracks,
    loadTracksFromApi,
    removeTrackFromExportQueue,
    trackItems,
    trackLoadState,
  } from '../utils/trackStore';
  import {
    getImportFileKind,
    SUPPORTED_IMPORT_HINT,
    type ImportFileKind,
  } from '../utils/trackData';

  type ExportFormat = 'gpx';

  let exportFormat: ExportFormat = 'gpx';
  let fileInput: HTMLInputElement | null = null;
  let selectedFile: File | null = null;
  let selectedFileKind: ImportFileKind | null = null;
  let importError: string | null = null;
  let importSuccess: string | null = null;
  let exportError: string | null = null;
  let exportSuccess: string | null = null;
  let isDragging: boolean = false;
  let isImporting: boolean = false;
  let isExporting: boolean = false;

  onMount(() => {
    void loadTracksFromApi();
  });

  function goToTracks(): void {
    push('/Tracks');
  }

  function openFilePicker(): void {
    fileInput?.click();
  }

  function handleFileInput(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    setSelectedFile(file);
  }

  function handleDragOver(event: DragEvent): void {
    event.preventDefault();
    isDragging = true;
  }

  function handleDragLeave(event: DragEvent): void {
    event.preventDefault();
    isDragging = false;
  }

  function handleDrop(event: DragEvent): void {
    event.preventDefault();
    isDragging = false;
    const file = event.dataTransfer?.files?.[0] ?? null;
    setSelectedFile(file);
  }

  function setSelectedFile(file: File | null): void {
    selectedFile = null;
    selectedFileKind = null;
    importError = null;
    importSuccess = null;

    if (!file) {
      return;
    }

    const detectedKind = getImportFileKind(file.name);
    if (!detectedKind) {
      importError = 'Unsupported file type. Upload a .gpx, .geojson, or .json file.';
      if (fileInput) {
        fileInput.value = '';
      }
      return;
    }

    selectedFile = file;
    selectedFileKind = detectedKind;
  }

  async function startImport(): Promise<void> {
    if (!selectedFile || !selectedFileKind) {
      importError = 'Choose a supported file before importing.';
      return;
    }

    isImporting = true;
    importError = null;
    importSuccess = null;

    try {
      const result = selectedFileKind === 'geojson'
        ? await importGeoJsonFile(selectedFile)
        : await importTracksGpx(selectedFile);

      if (result.status === 'error') {
        throw new Error(result.message || 'The backend rejected the import file.');
      }

      importSuccess = selectedFileKind === 'geojson'
        ? 'GeoJSON track import completed.'
        : 'GPX import completed.';

      selectedFile = null;
      selectedFileKind = null;
      if (fileInput) {
        fileInput.value = '';
      }

      await loadTracksFromApi();
    } catch (error: unknown) {
      importError = error instanceof Error ? error.message : 'Failed to import the selected file.';
    } finally {
      isImporting = false;
    }
  }

  async function startExport(): Promise<void> {
    if ($exportTrackIds.length === 0) {
      exportError = 'Queue at least one track before exporting.';
      return;
    }

    isExporting = true;
    exportError = null;
    exportSuccess = null;

    try {
      const fileBlob = await exportTracksGpx($exportTrackIds);
      const timestamp = new Date().toISOString().slice(0, 10);
      downloadBlob(fileBlob, `carputer-tracks-${timestamp}.${exportFormat}`);
      exportSuccess = `Downloaded ${$exportTrackCount} queued track${$exportTrackCount === 1 ? '' : 's'} as GPX.`;
    } catch (error: unknown) {
      exportError = error instanceof Error ? error.message : 'Failed to export the queued tracks.';
    } finally {
      isExporting = false;
    }
  }

  function downloadBlob(blob: Blob, fileName: string): void {
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = objectUrl;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(objectUrl);
  }

  async function importGeoJsonFile(file: File) {
    const text = await file.text();
    let parsedJson: unknown;

    try {
      parsedJson = JSON.parse(text);
    } catch {
      throw new Error('The selected JSON file is not valid JSON.');
    }

    return importTracksGeoJson(parsedJson);
  }
</script>

<main class="manage-data-shell">
  <AppBar title="Data Manager" />
  <button class="appbar-shortcut-btn" type="button" onclick={goToTracks}>Track Viewer</button>

  <section class="content-grid">
    <article class="panel">
      <div class="panel-header">
        <div>
          <h2>Export Tracks</h2>
        </div>
      </div>

      <div class="list-box">
        <div class="list-box-header">
          <div class="list-box-header-main">
            <h3>Export list</h3>
            <button class="action-btn action-btn--secondary" type="button" disabled={$exportTrackIds.length === 0} onclick={clearExportQueue}>Clear list</button>
          </div>
        </div>

        <ul class="queue-list">
          {#each $exportTracks as track (track.id)}
            <li class="queue-item">
              <div>
                <p class="queue-item-name">{track.name}</p>
                <p class="queue-item-meta">{track.date} &bull; {track.distanceMi.toFixed(1)} mi</p>
              </div>
              <button class="action-btn action-btn--secondary" type="button" onclick={() => removeTrackFromExportQueue(track.id)}>Remove</button>
            </li>
          {:else}
            <li class="queue-empty">No tracks queued yet. Add them from the track viewer.</li>
          {/each}
        </ul>
      </div>

      <div class="detail-box">
        <label class="field-label" for="export-format">Export format</label>
        <select id="export-format" class="field-input" bind:value={exportFormat}>
          <option value="gpx">GPX</option>
        </select>
      </div>

      <button class="action-btn action-btn--primary" type="button" disabled={$exportTrackIds.length === 0 || isExporting} onclick={startExport}>
        {isExporting ? 'Preparing export...' : 'Export queued tracks'}
      </button>

      {#if exportError}
        <p class="message message--error">{exportError}</p>
      {/if}
      {#if exportSuccess}
        <p class="message message--success">{exportSuccess}</p>
      {/if}
      {#if $trackLoadState.error}
        <p class="message message--error">{$trackLoadState.error}</p>
      {/if}
    </article>

    <article class="panel">
      <div class="panel-header">
        <div>
          <h2>Import Tracks</h2>
        </div>
      </div>

      <div
        class="drop-zone"
        class:drop-zone--active={isDragging}
        role="region"
        aria-label="Track import drop zone"
        ondragover={handleDragOver}
        ondragleave={handleDragLeave}
        ondrop={handleDrop}
      >
        <p class="drop-zone-title">Drag and drop a file here</p>
        <p class="drop-zone-copy">or browse for a GPX or GeoJSON file.</p>
        <button class="action-btn action-btn--secondary" type="button" onclick={openFilePicker}>Choose file</button>
        <input
          bind:this={fileInput}
          class="file-input"
          type="file"
          accept=".gpx,.geojson,.json,application/gpx+xml,application/json"
          onchange={handleFileInput}
        />
      </div>

      {#if selectedFile}
        <div class="selected-file">
          <p class="selected-file-name">{selectedFile.name}</p>
          <p class="selected-file-meta">Detected format: {selectedFileKind === 'gpx' ? 'GPX' : 'GeoJSON'}</p>
        </div>
      {/if}

      {#if importError}
        <p class="message message--error">{importError}</p>
      {/if}
      {#if importSuccess}
        <p class="message message--success">{importSuccess}</p>
      {/if}

      <button class="action-btn action-btn--primary" type="button" disabled={!selectedFile || isImporting} onclick={startImport}>
        {isImporting ? 'Uploading...' : 'Import file'}
      </button>
    </article>
  </section>
</main>

<style>
  .manage-data-shell {
    width: 100%;
    min-height: 100%;
    background: var(--surface-color, #eeeeee);
    color: var(--text-color, #111111);
    display: flex;
    flex-direction: column;
    position: relative;
  }

  .appbar-shortcut-btn {
    position: absolute;
    top: 0.85rem;
    right: 1rem;
    z-index: 30;
    border: 1px solid #ffffff;
    border-radius: 6px;
    background-color: var(--secondary-color, rgb(225, 225, 225));
    color: #222222;
    padding: 0.45rem 0.7rem;
    font: inherit;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s ease, box-shadow 0.2s ease;
  }

  .appbar-shortcut-btn:hover {
    background-color: #f1f1f1;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  }

  .content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1rem;
    padding: 1.25rem;
  }

  .panel {
    background-color: var(--primary-color, rgba(188, 188, 188, 0.9));
    border: 1px solid #ffffff;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .panel-header {
    display: flex;
    align-items: flex-start;
  }

  h2,
  h3,
  p {
    margin: 0;
  }

  .drop-zone-copy,
  .selected-file-meta,
  .queue-item-meta,
  .queue-empty {
    color: #38424f;
  }

  .detail-box,
  .list-box,
  .selected-file {
    background: rgba(255, 255, 255, 0.45);
    border-radius: 8px;
    padding: 0.85rem;
  }

  .detail-box {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .field-label {
    font-size: 0.9rem;
    font-weight: 600;
  }

  .field-input {
    width: 100%;
    padding: 0.55rem 0.7rem;
    border: 1px solid #b2b2b2;
    border-radius: 6px;
    font: inherit;
    background: #f5f5f5;
  }

  .queue-item-name,
  .selected-file-name,
  .drop-zone-title {
    font-weight: 700;
  }

  .list-box {
    display: flex;
    flex-direction: column;
    min-height: 0;
    border: 1px solid rgba(0, 0, 0, 0.15);
  }

  .list-box-header {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
    padding: 0.75rem 0.9rem;
    border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  }

  .list-box-header-main {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
  }

  .queue-list {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .queue-item,
  .queue-empty {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    padding: 0.85rem 0.9rem;
    border-top: 1px solid rgba(0, 0, 0, 0.08);
  }

  .queue-empty {
    justify-content: flex-start;
  }

  .drop-zone {
    display: grid;
    justify-items: start;
    gap: 0.55rem;
    padding: 1rem;
    border: 2px dashed #6f879b;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.4);
    transition: border-color 0.15s ease, background 0.15s ease;
  }

  .drop-zone--active {
    border-color: #1565c0;
    background: rgba(21, 101, 192, 0.08);
  }

  .selected-file {
    display: grid;
    gap: 0.2rem;
  }

  .message {
    padding: 0.7rem 0.8rem;
    border-radius: 8px;
    font-size: 0.9rem;
  }

  .message--error {
    background: rgba(198, 40, 40, 0.12);
    color: #8e1c1c;
  }

  .message--success {
    background: rgba(46, 125, 50, 0.14);
    color: #255c28;
  }

  .action-btn {
    width: fit-content;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font: inherit;
    font-weight: 600;
    transition: background-color 0.2s ease, box-shadow 0.2s ease;
  }

  .action-btn--primary {
    width: 100%;
    padding: 0.7rem 0.9rem;
    background-color: var(--secondary-color, rgb(225, 225, 225));
    color: #222222;
    text-align: center;
  }

  .action-btn--secondary {
    padding: 0.5rem 0.75rem;
    background-color: rgba(255, 255, 255, 0.75);
    color: #222222;
  }

  .action-btn:hover {
    background-color: #f1f1f1;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  }

  .action-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    box-shadow: none;
  }

  .file-input {
    display: none;
  }

  @media (max-width: 700px) {
    .appbar-shortcut-btn {
      top: 0.92rem;
      right: 0.6rem;
      padding: 0.4rem 0.6rem;
      font-size: 0.82rem;
    }

    .queue-item {
      flex-direction: column;
      align-items: flex-start;
    }

    .queue-item,
    .queue-empty {
      padding: 0.75rem;
    }
  }
</style>