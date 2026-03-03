<script>
  import BackButton from "../assets/components/BackButton.svelte";

</script>


<div class="translucent-overlay">
    
  <!-- this is the exit buttion -->
  <BackButton />

  <!-- this is a box to show the title -->
  <div class="title-box"> 
    <h2>Maps</h2>
  </div>

  <!-- for now it's just a button to download the map-->
  <button class=download-map-btn>Download Map</button>

</div>


<style>
  .translucent-overlay {
    position: absolute;
    inset:0;
    background: rgba(190, 190, 190, 0.3);
    z-index: 1000;
    backdrop-filter: blur(1.5px);
    overflow-y: auto;
  }

  .title-box {
    background: rgba(194, 194, 194, 0.9);
    text-align: center;
    border: 2px solid rgba(0, 0, 0, 1);
    color: rgb(0, 0, 0);
  }

  .download-map-btn {
    position:relative; 
    margin-top: 5%; 
    left: 5%;
    background-color: lightgrey;
  }

</style>
