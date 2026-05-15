<script lang="ts">
  import BackButton from "../assets/components/BackButton.svelte";
  import DarkLightIndicator from "../assets/components/DarkLightIndicator.svelte";
  import SystemIndicators from "../assets/components/SystemIndicators.svelte";
  import {
    settingsPreferences,
    updateSettingsPreferences,
    type TrackRange,
  } from "../services/settings_preferences";


  function handleToggleAllTracks(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updateSettingsPreferences({ areAllTracksOn: input.checked });
  }

  function handleToggleAprsPoints(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updateSettingsPreferences({ areAprsPointsOn: input.checked });
  }

  function handleMilesChange(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updateSettingsPreferences({ milesToDiscoverRoads: Number(input.value) });
  }

  function handleNightModeChange(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updateSettingsPreferences({ nightMode: input.checked });
  }

  function handleBrightnessChange(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updateSettingsPreferences({ brightness: Number(input.value) });
  }

  function handleTrackRange(range: TrackRange) : void {
    updateSettingsPreferences({ trackRange: range});
  }

  function handleSelectedTrackColorChange(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updateSettingsPreferences({ selectedTrackColor: input.value });
  }

  function handleRestingTrackColorChange(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updateSettingsPreferences({ restingTrackColor: input.value });
  }

  function handleTrackThicknessChange(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updateSettingsPreferences({ trackThickness: Number(input.value) });
  }

  // defaultZoom stored as 12–21; displayed as 1–10 (display = zoom - 11)
  function incrementZoom(): void {
    settingsPreferences.update((p) => ({ ...p, defaultZoom: Math.min(21, p.defaultZoom + 1) }));
  }

  function decrementZoom(): void {
    settingsPreferences.update((p) => ({ ...p, defaultZoom: Math.max(12, p.defaultZoom - 1) }));
  }

  function incrementIconSize(): void {
    settingsPreferences.update((p) => ({ ...p, iconSizeLevel: Math.min(5, p.iconSizeLevel + 1) }));
  }

  function decrementIconSize(): void {
    settingsPreferences.update((p) => ({ ...p, iconSizeLevel: Math.max(1, p.iconSizeLevel - 1) }));
  }

</script>


<div class="translucent-overlay">
  <!-- this contains everything for settins -->
  <div>
    <!-- this is a box to show the title -->
    <div class="title-box"> 
        <!-- this is the exit buttion -->
        <BackButton />
      <h2>Track Settings</h2>

      <SystemIndicators 
        isActiveBackground={false} 
        isDarklightActive={false} 
        isRoadDiscoverActive={false}
      />
    </div>

    
    <div class="option-box">
      <h3>All Tracks</h3>
      <div class="switch-controls">
        <label class="switch">
          <input
            type="checkbox"
            checked={$settingsPreferences.areAllTracksOn}
            on:change={handleToggleAllTracks}
          />
          <i class={$settingsPreferences.areAllTracksOn ? "iconoir-switch-on" : "iconoir-switch-off"}></i>
        </label>
        <h3 class={$settingsPreferences.areAllTracksOn ? "toggle_text_on" : "toggle_text_off"}>
          {$settingsPreferences.areAllTracksOn ? "ON" : "OFF"}
        </h3>
      </div>
    </div>

    <div class="option-box">
      <h3>APRS Pin Points</h3>
      <div class="switch-controls">
        <label class="switch">
          <input
            type="checkbox"
            checked={$settingsPreferences.areAprsPointsOn}
            on:change={handleToggleAprsPoints}
          />
          <i class={$settingsPreferences.areAprsPointsOn ? "iconoir-switch-on" : "iconoir-switch-off"}></i>
        </label>
        <h3 class={$settingsPreferences.areAprsPointsOn ? "toggle_text_on" : "toggle_text_off"}>
          {$settingsPreferences.areAprsPointsOn ? "ON" : "OFF"}
        </h3>
      </div>
    </div>
    
    <div class="option-box">
      <h3>Road History Within</h3>
      
      <div class="controls">
        <input
          type="range"
          min="0"
          max="100"
          value={$settingsPreferences.milesToDiscoverRoads}
          step="5"
          on:input={handleMilesChange}
        >
        
        <span style="text-align: right; width: 30px;"><b>{$settingsPreferences.milesToDiscoverRoads}</b></span>
        <b>miles</b>
      </div>
    </div>

    <div class="option-box">
      <h3>Track History</h3>

      <div class="range-buttons">
        <button
          class:selected={$settingsPreferences.trackRange === "day"}
          on:click={() => handleTrackRange("day")}
        >
          Day
        </button>

        <button
          class:selected={$settingsPreferences.trackRange === "week"}
          on:click={() => handleTrackRange("week")}
        >
          Week
        </button>

        <button
          class:selected={$settingsPreferences.trackRange === "month"}
          on:click={() => handleTrackRange("month")}
        >
          Month
        </button>

        <button
          class:selected={$settingsPreferences.trackRange === "year"}
          on:click={() => handleTrackRange("year")}
        >
          Year
        </button>

        <button
          class:selected={$settingsPreferences.trackRange === "all"}
          on:click={() => handleTrackRange("all")}
        >
          All
        </button>
      </div>
    </div>

    <div class="option-box">
      <h3>Selected Track Color</h3>

      <div class="controls">
        <input
          type="color"
          value={$settingsPreferences.selectedTrackColor}
          on:input={handleSelectedTrackColorChange}
        />
        <span class="color-value"><b>{$settingsPreferences.selectedTrackColor}</b></span>
      </div>
    </div>

    <div class="option-box">
      <h3>Resting Track Color</h3>

      <div class="controls">
        <input
          type="color"
          value={$settingsPreferences.restingTrackColor}
          on:input={handleRestingTrackColorChange}
        />
        <span class="color-value"><b>{$settingsPreferences.restingTrackColor}</b></span>
      </div>
    </div>

    <div class="option-box">
      <h3>Track Thickness</h3>

      <div class="controls">
        <input
          type="range"
          min="1"
          max="12"
          value={$settingsPreferences.trackThickness}
          step="1"
          on:input={handleTrackThicknessChange}
        >
        <span style="text-align: right; width: 44px;"><b>{$settingsPreferences.trackThickness}px</b></span>
      </div>
    </div>
  </div>


  <!-- this contains everything for settins -->
  <div>
    <!-- This page will also have a Preferences title -->
    <div class="title-box" style="margin-top: 10%;"> 
      <h2>System Preferences</h2>
    </div>

    <div class="option-box">
      <h3>Night Mode</h3>
      <span class="icon">
        <DarkLightIndicator />
      </span>
      <div class="switch-controls">
        <label class="switch">
          <input
            type="checkbox"
            checked={$settingsPreferences.nightMode}
            on:change={handleNightModeChange}
          />
          <i class={$settingsPreferences.nightMode ? "iconoir-switch-on" : "iconoir-switch-off"}></i>
        </label>
        <h3 class={$settingsPreferences.nightMode ? "toggle_text_on" : "toggle_text_off"}>
          {$settingsPreferences.nightMode ? "ON" : "OFF"}
        </h3>
      </div>
    </div>

    <div class="option-box">
      <h3>Brightness</h3>
      
      <div class="controls">
        <input
          type="range"
          min="10"
          max="100"
          value={$settingsPreferences.brightness}
          step="5"
          on:input={handleBrightnessChange}
        >
        <span style="text-align: right; width: 52px;"><b>{$settingsPreferences.brightness}%</b></span>
      </div>
    </div>

    <div class="option-box">
      <h3>Default Lock Zoom</h3>
      
      <div class="controls">
        <button class="zoom-btn" on:click={decrementZoom} disabled={$settingsPreferences.defaultZoom <= 12}>−</button>
        <span class="zoom-value"><b>{$settingsPreferences.defaultZoom - 11}</b></span>
        <button class="zoom-btn" on:click={incrementZoom} disabled={$settingsPreferences.defaultZoom >= 21}>+</button>
      </div>
    </div>

    <div class="option-box">
      <h3>My Icon Size</h3>

      <div class="controls">
        <button class="zoom-btn" on:click={decrementIconSize} disabled={$settingsPreferences.iconSizeLevel <= 1}>−</button>
        <span class="zoom-value"><b>{$settingsPreferences.iconSizeLevel}</b></span>
        <button class="zoom-btn" on:click={incrementIconSize} disabled={$settingsPreferences.iconSizeLevel >= 5}>+</button>
      </div>
    </div>
  </div>


</div>


<style>
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

  .controls input[type="color"] {
    width: 48px;
    height: 34px;
    padding: 0;
    border: 1px solid #777;
    cursor: pointer;
    background: transparent;
  }

  .color-value {
    min-width: 70px;
    text-transform: lowercase;
  }

  .icon {
    display: flex;
    align-items: center;
    margin-right:auto;
  }

  .switch {
    cursor: pointer;
    color: #333;
    display: inline-block;
    user-select: none;
    -webkit-user-select: none;
  }

  .switch input {
    display: none;
  }

  .switch i {
    font-size: 44px;
    display: inline-block;
    cursor: pointer;
  }

  .switch-controls {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .toggle_text_on {
    color: rgb(33, 140, 0);
    font-size: 18px;
    width: 50px;
    margin: 0;
  }

  .toggle_text_off {
    color: rgb(180, 42, 0);
    font-size: 18px;
    width: 50px;
    margin: 0;
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

  .range-buttons {
    display: flex;
    gap: 8px;
  }

  .range-buttons button {
    padding: 6px 12px;
    -webkit-text-fill-color: black;
    border: 1px solid #ccc;
    background: rgb(130, 130, 130);
    cursor: pointer;
    outline: none;
  }

  .range-buttons button.selected {
    background: rgb(100, 100, 100);
    -webkit-text-fill-color: white;
  }

</style>
