<script lang="ts">
  import { settingsPreferences } from "../../services/settings_preferences";

  //images to use
  import light_mode from "../icons/light-mode-bold.svg";
  import dark_mode from "../icons/dark-mode-bold.svg";

</script>


<!-- dark/light mode-->
<div class="indicator">
  {#if $settingsPreferences.nightMode}
      <img src={dark_mode} alt="dark_mode_indicator" style="width:24px; height:24px;" />
  {:else}
    <img src={light_mode} alt="light_mode_indicator" style="width:24px; height:24px;" />
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