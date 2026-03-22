<script lang="ts">
  //import { systemInfo } from "some place that catches information from backend"

  //images to use
  import wifi0 from "../wifi-signal0-bold.svg";
  import wifi1 from "../wifi-signal1-bold.svg";
  import wifi2 from "../wifi-signal2-bold.svg";
  import wifi3 from "../wifi-signal3-bold.svg";
  import light_mode from "../light-mode-bold.svg";
  import dark_mode from "../dark-mode-bold.svg";

  // delete this after the indicators are implemented with backend information.
  let darkMode:boolean = false 

</script>


<!-- dark/light mode-->
<div class="indicator">
  {#if darkMode}
      <img src={dark_mode} alt="dark_mode_indicator" style="width:24px; height:24px;" />
  {:else}
    <img src={light_mode} alt="light_mode_indicator" style="width:24px; height:24px;" />
  {/if}
</div>



<style>
  .indicator {
    display: flex;
    align-items: center;
    justify-content: space-evenly;
    gap: 5px;
    width: 30px;
  }

</style>