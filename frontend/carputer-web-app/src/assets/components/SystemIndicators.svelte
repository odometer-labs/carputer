<script lang="ts">
  import TimeIndicator from "./TimeIndicator.svelte";
  import RoadDiscoverIndicator from "./RoadDiscoverIndicator.svelte";
  import WifiIndicator from "./WifiIndicator.svelte";
  import DarkLightIndicator from "./DarkLightIndicator.svelte";


  export let isTimeActive: boolean = true;
  export let isWifiActive: boolean = true;
  export let isDarklightActive: boolean = true;
  export let isRoadDiscoverActive: boolean = true;
  export let isActiveBackground: boolean = true;

</script>


<div class={isActiveBackground? "status-bar": "status-bar-translucent"}>
  <!-- time -->
  {#if isTimeActive}
    <TimeIndicator />
  {/if}

  <!-- wifi-->
  {#if isWifiActive}
    <WifiIndicator />
  {/if}

  <!-- dark/light mode-->
  {#if isDarklightActive}
    <DarkLightIndicator />
  {/if}

  <!--on new road or old road-->
  {#if isRoadDiscoverActive}
    <RoadDiscoverIndicator />
  {/if}
</div>



<style>
  .status-bar {
    position: absolute; 
    top: 27px; 
    right: 200px; 
    z-index: 1000;

    display: flex;
    align-items: center;
    gap: 20px;
    padding: 10px 15px 10px 15px;

    background-color: rgb(188, 188, 188, 0.9);
    -webkit-text-fill-color: black;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2); 
    border: 1px solid white;
    border-radius: 4px;
  }

 .status-bar-translucent {
    position: absolute; 
    top: 20px; 
    right: 200px; 
    z-index: 1000;

    display: flex;
    align-items: center;
    gap: 25px;
    padding: 15px;

    -webkit-text-fill-color: black;
 }

</style>