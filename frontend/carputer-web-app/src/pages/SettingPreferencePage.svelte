<script lang="ts">
  import BackButton from "../assets/components/BackButton.svelte";
  import DarkLightIndicator from "../assets/components/DarkLightIndicator.svelte";
  import SystemIndicators from "../assets/components/SystemIndicators.svelte";
  import {
    preferences,
    updatePreferences,
  } from "../services/preferences";


  function handleToggleAllTracks(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updatePreferences({ toggleAllTracks: input.checked });
  }

  function handleMilesChange(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updatePreferences({ milesToDiscoverRoads: Number(input.value) });
  }

  function handleNightModeChange(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updatePreferences({ nightMode: input.checked });
  }

  function handleBrightnessChange(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updatePreferences({ brightness: Number(input.value) });
  }

  function handleTracksAfterDateChange(event: Event) : void {
    const input = event.currentTarget as HTMLInputElement;

    updatePreferences({
      showTracksAfterDate: input.value ? input.value : null
    });
  }

  function handleTracksBeforeDateChange(event: Event) : void {
    const input = event.currentTarget as HTMLInputElement;

    updatePreferences({
      showTracksBeforeDate: input.value ? input.value : null
    });
  }

  // defaultZoom stored as 12–21; displayed as 1–10 (display = zoom - 11)
  function incrementZoom(): void {
    preferences.update((p) => ({ ...p, defaultZoom: Math.min(21, p.defaultZoom + 1) }));
  }

  function decrementZoom(): void {
    preferences.update((p) => ({ ...p, defaultZoom: Math.max(12, p.defaultZoom - 1) }));
  }

  function incrementIconSize(): void {
    preferences.update((p) => ({ ...p, iconSizeLevel: Math.min(5, p.iconSizeLevel + 1) }));
  }

  function decrementIconSize(): void {
    preferences.update((p) => ({ ...p, iconSizeLevel: Math.max(1, p.iconSizeLevel - 1) }));
  }

</script>


<div class="translucent-overlay">
  <!-- this contains everything for settins -->
  <div>
    <!-- this is a box to show the title -->
    <div class="title-box"> 
        <!-- this is the exit buttion -->
        <BackButton />
      <h2>Settings</h2>

      <SystemIndicators 
        isActiveBackground={false} 
        isDarklightActive={false} 
        isRoadDiscoverActive={false}
      />
    </div>

    <!-- the box contains a settings functionality 
        THIS IS ALL JUST TEMPORARY, I JUST DIDN'T WANT THIS PAGE
        TO BE EMPY                                              -->
    <div class="option-box">
      <h3>Togle All Tracks</h3>
      <input
        type="checkbox"
        class="checkbox"
        checked={$preferences.toggleAllTracks}
        on:change={handleToggleAllTracks}
      />
    </div>
    
    <div class="option-box">
      <h4>Road History</h4>
      
      <div class="controls">
        <input
          type="range"
          min="0"
          max="100"
          value={$preferences.milesToDiscoverRoads}
          step="5"
          on:input={handleMilesChange}
        >
        <span style="text-align: right; width: 30px;"><b>{$preferences.milesToDiscoverRoads}</b></span>
      </div>
    </div>

    <div class="option-box">
      <h4>Show Tracks After:</h4>

      <div>
        <input
          type="date"
          value={$preferences.showTracksAfterDate ?? ""}
          on:change={handleTracksAfterDateChange}
        />

        <button 
          on:click={() => updatePreferences({ showTracksAfterDate: null })}
          class="date-btn"
        >
          Clear
        </button>
      </div>
    </div>

    <div class="option-box">
      <h4>Show Tracks Before:</h4>

      <div>
        <input
          type="date"
          value={$preferences.showTracksBeforeDate ?? ""}
          on:change={handleTracksBeforeDateChange}
        />

        <button 
          on:click={() => updatePreferences({ showTracksBeforeDate: null })}
          class="date-btn"
        >
          Clear
        </button>
      </div>
    </div>
  </div>


  <!-- this contains everything for settins -->
  <div>
    <!-- This page will also have a Preferences title -->
    <div class="title-box" style="margin-top: 10%;"> 
      <h2>Preferences</h2>
    </div>

    <!-- the box contains a preferences functionality
        THIS IS ALL JUST TEMPORARY, I JUST DIDN'T WANT THIS PAGE
        TO BE EMPY                                              -->
    <div class="option-box">
      <h3>Night Mode</h3>
      <span class="icon">
        <DarkLightIndicator />
      </span>
      <input
        type="checkbox"
        class="checkbox"
        checked={$preferences.nightMode}
        on:change={handleNightModeChange}
      />
    </div>

    <div class="option-box">
      <h3>Brightness</h3>
      
      <div class="controls">
        <input
          type="range"
          min="10"
          max="100"
          value={$preferences.brightness}
          step="5"
          on:input={handleBrightnessChange}
        >
        <span style="text-align: right; width: 52px;"><b>{$preferences.brightness}%</b></span>
      </div>
    </div>

    <div class="option-box">
      <h3>Default Lock Zoom</h3>
      
      <div class="controls">
        <button class="zoom-btn" on:click={decrementZoom} disabled={$preferences.defaultZoom <= 12}>−</button>
        <span class="zoom-value"><b>{$preferences.defaultZoom - 11}</b></span>
        <button class="zoom-btn" on:click={incrementZoom} disabled={$preferences.defaultZoom >= 21}>+</button>
      </div>
    </div>

    <div class="option-box">
      <h3>Icon Size</h3>

      <div class="controls">
        <button class="zoom-btn" on:click={decrementIconSize} disabled={$preferences.iconSizeLevel <= 1}>−</button>
        <span class="zoom-value"><b>{$preferences.iconSizeLevel}</b></span>
        <button class="zoom-btn" on:click={incrementIconSize} disabled={$preferences.iconSizeLevel >= 5}>+</button>
      </div>
    </div>
  </div>


</div>


<style>

  .checkbox {
    transform: scale(1.5);
  }
  .option-box {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid rgba(0, 0, 0, 0.5);
    border-bottom: 1px solid rgba(0, 0, 0, 0.5);
    padding-left: 5%;
    padding-right: 5%;
    color: black;
    gap: 10px;
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-left: auto;
  }
  .controls input[type="range"] {
    width: 250px;
  }

  .icon {
    display: flex;
    align-items: center;
    margin-right:auto;
  }

  .zoom-btn {
    width: 36px;
    height: 36px;
    font-size: 1.3rem;
    -webkit-text-fill-color: black;
    line-height: 1;
    background-color: rgb(130, 130, 130);
    border: 1px solid #ccc; 
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    outline: none;
  }
  .zoom-btn:active {
    background-color: rgb(100, 100, 100);
  }
  .zoom-value {
    min-width: 24px;
    text-align: center;
    font-size: 1.1rem;
  }

  .date-btn {
    height: 28px;
    padding: 0 8px;
    font-size: 0.85rem;
    -webkit-text-fill-color: black;
    border: 1px solid #ccc;
    background: rgb(130, 130, 130);
    cursor: pointer;
    align-items: center;
    outline: none;
  }
  .date-btn:active {
    background-color: rgb(100, 100, 100);
  }

</style>
