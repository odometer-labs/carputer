<script lang="ts">
  // TODO : get the refernce to the information from back end so that we can
  //  know if the user is on a new road or not.
  //import { systemInfo } from "some place that catches information from backend"

  // delete this after the indicators are implemented with backend information.
  let isOnNewRoad:boolean = false

  //this just changes old/new road indicator to showcase what they look
  //delete this after getting real data.
  import { onMount } from "svelte";
  onMount(() => {
    const interval = setInterval(() => {
      isOnNewRoad = !isOnNewRoad
    }, 3000); // 3 seconds

    return () => clearInterval(interval);
  });
</script>


<!--on new road or old road-->
<div class="indicator">
  {#if isOnNewRoad}
    <strong>new</strong>
  {:else}
    <strong>old</strong>
  {/if}
    <strong>road</strong>
</div>



<style>
  .indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    width: 70px;
  }

</style>