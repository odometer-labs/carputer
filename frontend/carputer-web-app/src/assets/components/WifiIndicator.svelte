<script lang="ts">
  import wifi0 from "../icons/wifi-signal0-bold.svg";
  import wifi1 from "../icons/wifi-signal1-bold.svg";
  import wifi2 from "../icons/wifi-signal2-bold.svg";
  import wifi3 from "../icons/wifi-signal3-bold.svg";
  import { wifiStore } from "../../stores/wifiStore";

  const wifiIcons = [wifi0, wifi1, wifi2, wifi3];

  // Map 0-100 percentage to icon index 0-3
  $: iconIndex = !$wifiStore.isConnected ? 0
    : $wifiStore.signalStrength >= 67 ? 3
    : $wifiStore.signalStrength >= 34 ? 2
    : 1;
</script>


<!-- wifi-->
<div class="indicator">
  <img src={wifiIcons[iconIndex]}
    alt={`wifi-${iconIndex}`} style="width:24px; height:24px;"
  />
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