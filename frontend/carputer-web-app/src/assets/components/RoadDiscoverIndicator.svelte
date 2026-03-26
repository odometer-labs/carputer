<script lang="ts">
  // TODO : get the refernce to the information from back end so that we can
  //  know if the user is on a new road or not.
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
    <strong>road</strong>
</div>



<style>
  .indicator {
    gap: 5px;
    width: 70px;
  }

</style>