<script lang="ts">
  import SpeedIndicator from "./SpeedIndicator.svelte";
  import TimeIndicator from "./TimeIndicator.svelte";
  import RoadDiscoverIndicator from "./RoadDiscoverIndicator.svelte";
  import WifiIndicator from "./WifiIndicator.svelte";
  import DarkLightIndicator from "./DarkLightIndicator.svelte";

</script>

<div>
  <div class="status-bar" {...$$restProps}>
    <!-- time -->
    <strong>10:30</strong>
    <!-- wifi-->
    <WifiIndicator />

    <!-- dark/light mode-->
    <DarkLightIndicator />

    <!--on new road or old road-->
    <RoadDiscoverIndicator />
  </div>

  <SpeedIndicator />
</div>






<style>
  .status-bar {
    position: absolute; 
    top: 10px; 
    right: 200px; 
    z-index: 1000;

    display: flex;
    gap: 15px;
    padding: 10px;

    background-color: rgb(188, 188, 188, 0.9);
    -webkit-text-fill-color: black;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2); 
    border: 1px solid white;
    border-radius: 4px;
  }

  .indicator {
    display: flex;
    align-items: center;
    justify-content: space-evenly;
    gap: 5px;
    width: 30px;
  }

</style>