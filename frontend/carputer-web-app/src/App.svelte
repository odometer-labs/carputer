<script>
  import OpenlayersMap from './pages/OpenlayersMap.svelte';

  let openlayersMapComponent;

  function handleSnapToLocation() {
    if(openlayersMapComponent){
      openlayersMapComponent.snapToUserLocation();
    }
  }

</script>


<main style="margin: 0; padding: 0; height: 100%; width: 100%;">
  <OpenlayersMap bind:this={openlayersMapComponent} />

  <div class="header">
    <button on:click={handleSnapToLocation}>Snap to My Location</button>
  </div>

</main>

<style>
  .header {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  button {
    padding: 10px 20px;
    font-size: 14px;
    cursor: pointer;
    border: none;
    border-radius: 8px;
    background-color: rgba(255, 255, 255, 0.9);
    color: #333;
    font-weight: 500;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    transition: all 0.2s;
  }

  button:hover {
    background-color: rgba(255, 255, 255, 1);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
  }
</style>

