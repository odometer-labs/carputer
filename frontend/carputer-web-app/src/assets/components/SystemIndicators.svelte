<script lang="ts">
  import TimeIndicator from "./TimeIndicator.svelte";
  import RoadDiscoverIndicator from "./RoadDiscoverIndicator.svelte";
  import WifiIndicator from "./WifiIndicator.svelte";
  import DarkLightIndicator from "./DarkLightIndicator.svelte";


  export let timeActive: boolean = true;
  export let wifiActive: boolean = true;
  export let darklightActive: boolean = true;
  export let roadDiscoverActive: boolean = true;
  export let isActiveBackground: boolean = true;

</script>


<div class={isActiveBackground? "status-bar": "status-bar-translucent"}>
  <!-- time -->
  {#if timeActive}
    <TimeIndicator />
  {/if}

  <!-- wifi-->
  {#if wifiActive}
    <WifiIndicator />
  {/if}

  <!-- dark/light mode-->
  {#if darklightActive}
    <DarkLightIndicator />
  {/if}

  <!--on new road or old road-->
  {#if roadDiscoverActive}
    <RoadDiscoverIndicator />
  {/if}
</div>



<style>
  .status-bar {
    position: absolute; 
    top: 20px; 
    right: 200px; 
    z-index: 1000;

    display: flex;
    gap: 25px;
    padding: 15px;

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
    gap: 25px;
    padding: 15px;

    -webkit-text-fill-color: black;
 }

</style>