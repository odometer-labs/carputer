<script lang="ts">
  import { trackStore } from "../../stores/trackStore";
</script>


<!--on new road or old road-->
<div class="indicator">
  {#if $trackStore.isOnNewRoad}
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