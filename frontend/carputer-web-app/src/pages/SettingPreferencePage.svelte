<script>
  import { onMount } from "svelte";
  import BackButton from "../assets/components/BackButton.svelte";
  import {
    DEFAULT_PREFERENCES,
    loadPreferences,
    savePreferences,
  } from "../services/preferences";

  let toggleSomething = DEFAULT_PREFERENCES.toggleSomething;
  let milesToDiscoverRoads = DEFAULT_PREFERENCES.milesToDiscoverRoads;
  let nightMode = DEFAULT_PREFERENCES.nightMode;
  let hasLoadedPreferences = false;

  onMount(() => {
    const persistedPreferences = loadPreferences();
    toggleSomething = persistedPreferences.toggleSomething;
    milesToDiscoverRoads = persistedPreferences.milesToDiscoverRoads;
    nightMode = persistedPreferences.nightMode;
    hasLoadedPreferences = true;
  });

  $: if (hasLoadedPreferences) {
    savePreferences({
      toggleSomething,
      milesToDiscoverRoads,
      nightMode,
    });
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
      <input type="checkbox" style="margin-left: auto;" bind:checked={toggleSomething} />
    </div>
    
    <div class="option-box">
      <h3>Miles to Discover Roads</h3>
      
      <div class="controls">
        <input type="range" min="0" max="100" bind:value={milesToDiscoverRoads} step="5">
        <span style="text-align: right; width: 30px;"><b>{milesToDiscoverRoads}</b></span>
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
      <input type="checkbox" style="margin-left: auto;" bind:checked={nightMode} />
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
