<script lang="ts">
  //import { systemInfo } from "some place that catches information from backend"

  // delete this after the indicators are implemented with backend information.
  let onNewRoad:boolean = false

</script>


<!--on new road or old road-->
<div class="indicator">
  {#if onNewRoad}
    <strong>new</strong>
  {:else}
    <strong>old</strong>
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