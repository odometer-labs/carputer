<script lang="ts">
  //TODO : in the future when we get information about the wifi we need to
  // access it here to let the user know what the wifi strength is.
  //import { systemInfo } from "some place that catches information from backend"

  //images to use
  import wifi0 from "../wifi-signal0-bold.svg";
  import wifi1 from "../wifi-signal1-bold.svg";
  import wifi2 from "../wifi-signal2-bold.svg";
  import wifi3 from "../wifi-signal3-bold.svg";

  // delete this after the indicators are implemented with backend information.
  let wifiConnection:boolean = true
  let wifiConnection_strength:number = 3; // 0-3

  const wifiIcons = [wifi0, wifi1, wifi2, wifi3];
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
    gap: 5px;
    width: 30px;
  }

</style>