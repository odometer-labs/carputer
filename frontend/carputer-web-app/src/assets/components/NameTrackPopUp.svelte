<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
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
    <div class="track-popup-overlay">
      <div class="track-popup">
        <h3>Name Your Track</h3>
        <input
          type="text"
          style="outline: none;"
          bind:value={trackName}
          placeholder="Enter track name..."
          maxlength="50"
          bind:this={inputEl}
        />
        <div class="track-popup-buttons">
          <button on:click={confirmTrackName}>Save</button>
          <button on:click={cancelTrackName}>Cancel</button>
        </div>
      </div>
    </div>
  {/if}
</main>

<style>
  .track-popup-overlay {
    position: absolute;
    inset: 0;
    background: rgba(188, 188, 188, 0.45);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2000;
  }

  .track-popup {
    background-color: rgb(188, 188, 188);
    padding: 20px;
    border-radius: 12px;
    width: 280px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3);
    text-align: center;
  }

  .track-popup h3 {
    margin-top: 0;
    margin-bottom: 12px;
    color: black;
  }

  .track-popup input {
    width: 100%;
    padding: 10px;
    margin-bottom: 14px;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-size: 14px;
    box-sizing: border-box;
  }

  .track-popup-buttons {
    display: flex;
    justify-content: space-between;
    gap: 10px;
  }

  .track-popup-buttons button {
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
  .track-popup-buttons button:active {
    background-color: rgb(100, 100, 100);
  }
</style>
