<script lang="ts">
  //import { preferences } from "../services/preferences"; //import the svelte store for preferences
  //import { systemInfo } from "some place that catches information from backend"

  // delete this after the indicators are implemented with backend information.
  let darkMode:boolean = false 
  let wifiConnection:boolean = false
  let onNewRoad:boolean = false
</script>


<div class="status-bar" {...$$restProps}>
  <!-- wifi-->
  <div class="indicator">
    {#if wifiConnection}
      <i class="iconoir-wifi"></i>
    {:else}
      <i class="iconoir-wifi-off"></i>
    {/if}
  </div>

  <!-- dark/light mode-->
  <div class="indicator">
    {#if darkMode}
      <i class="iconoir-half-moon"></i>
    {:else}
      <i class="iconoir-bright-star"></i>
    {/if}
  </div>

  <!--on new road or old road-->
  <div class="indicator">
    {#if onNewRoad}
      <i>new</i>
    {:else}
      <i>old</i>
    {/if}
  </div>
</div>



<style>
  .status-bar {
    position: absolute; 
    top: 100px; 
    right: 20px; 
    z-index: 1000;

    display: flex;
    flex-direction: column;
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