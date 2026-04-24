<script lang="ts">
  //TODO : in the future when we get information about the wifi we need to
  // access it here to let the user know what the wifi strength is.
  //import { systemInfo } from "some place that catches information from backend"

  //images to use
  import wifi0 from "../icons/wifi-signal0-bold.svg";
  import wifi1 from "../icons/wifi-signal1-bold.svg";
  import wifi2 from "../icons/wifi-signal2-bold.svg";
  import wifi3 from "../icons/wifi-signal3-bold.svg";

  // delete this after the indicators are implemented with backend information.
  let wifiConnection:boolean = true
  let wifiConnection_strength:number = 3; // 0-3

  const wifiIcons = [wifi0, wifi1, wifi2, wifi3];

  //this just changes the wifi indicator with setinterval 
  //delete this after getting real data.
  import { onMount } from "svelte";
  onMount(() => {
    const interval = setInterval(() => {
      // cycle from 0 → 3
      wifiConnection_strength = (wifiConnection_strength + 1) % 4;
    }, 3000); // 3 seconds

    return () => clearInterval(interval);
  });

</script>


<!-- wifi-->
<div class="indicator">
  {#if wifiConnection}
    <img src={wifiIcons[wifiConnection_strength]} 
      alt={`wifi-${wifiConnection_strength}`} style="width:24px; height:24px;" 
    />
  {:else}
    <img src={wifi0} alt="wifi-3" style="width:24px; height:24px;" />
  {/if}
</div>



<style>
  .indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    width: 30px;
  }

</style>