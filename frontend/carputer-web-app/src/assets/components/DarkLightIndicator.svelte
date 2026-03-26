<script lang="ts">
  // TODO : add a refernce to the preference store so that we can know when the dark/light mode is active.
  //import { systemInfo } from "some place that catches information from backend"

  //images to use
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
    gap: 5px;
    width: 30px;
  }

</style>