<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import '../styles/popups.css';
  export let show: boolean = false;
  export let pendingFinalize: boolean = false;
  export let initialTrackName: string = "";

  const dispatch = createEventDispatcher();
  let trackName: string = initialTrackName;

  // Focus input when popup is shown
  let inputEl: HTMLInputElement | null = null;
  onMount(() => {
    if (show && inputEl) inputEl.focus();
  });

  function confirmTrackName() {
    if (!pendingFinalize) return;
    let name = trackName && trackName.trim() !== "" ? trackName : `Track ${new Date().toLocaleString()}`;
    dispatch('confirm', { trackName: name });
    trackName = "";
  }

  function cancelTrackName() {
    dispatch('cancel');
    trackName = "";
  }
</script>
<main>
  {#if show}
    <div class="popup-overlay">
      <div class="popup-container" style="width: 280px;">
        <h3 class="popup-title track-popup-title">Name Your Track</h3>
        <input
          type="text"
          class="popup-input"
          bind:value={trackName}
          placeholder="Enter track name..."
          maxlength="50"
          bind:this={inputEl}
        />
        <div class="popup-buttons-container">
          <button class="track-button" on:click={confirmTrackName}>Save</button>
          <button class="track-button" on:click={cancelTrackName}>Cancel</button>
        </div>
      </div>
    </div>
  {/if}
</main>

<style>
  /* Component-specific adjustments only */
  .track-popup-title {
    text-align: center;
    margin-bottom: 12px;
    margin-top: 0;
  }

  .track-button {
    flex: content;
    padding: 10px;
    border-radius: 8px;
    font-size: 1.3rem;
    -webkit-text-fill-color: black;
    line-height: 1;
    background-color: rgb(130, 130, 130);
    border: 1px solid #ccc;
    cursor: pointer;
    align-items: center;
    justify-content: center;
    outline: none;
  }

  .track-button:active {
    background-color: rgb(100, 100, 100);
  }
</style>
