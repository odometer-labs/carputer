<script lang="ts">
  import BackButton from "../assets/components/BackButton.svelte";
  import {
    preferences,
    updatePreferences,
  } from "../services/preferences";

  function handleToggleSomethingChange(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    updatePreferences({ toggleSomething: input.checked });
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

</script>


<div class="translucent-overlay">

  <!-- this is the exit buttion -->
  <BackButton />

  <!-- this contains everything for settins -->
  <div>
    <!-- this is a box to show the title -->
    <div class="title-box"> 
      <h2>Settings</h2>
    </div>

    <!-- the box contains a settings functionality 
        THIS IS ALL JUST TEMPORARY, I JUST DIDN'T WANT THIS PAGE
        TO BE EMPY                                              -->
    <div class="option-box">
      <h3>Togle something</h3>
      <input
        type="checkbox"
        style="margin-left: auto;"
        checked={$preferences.toggleSomething}
        on:change={handleToggleSomethingChange}
      />
    </div>
    
    <div class="option-box">
      <h3>Miles to Discover Roads</h3>
      
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
      <input
        type="checkbox"
        style="margin-left: auto;"
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
  </div>
</div>


<style>
  .option-box {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid rgba(0, 0, 0, 0.5);
    padding-left: 5%;
    padding-right: 5%;
    color: black;
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

</style>
