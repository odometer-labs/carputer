<script>
  import { push } from 'svelte-spa-router';

  
  // Function to navigate back to the home map page
  function goBack() {
    push('/');
  }

</script>


<div class="translucent-overlay">
    
  <!-- this is the exit buttion -->
  <!-- svelte-ignore a11y_consider_explicit_label -->
  <button style="position:absolute; top:2%; left:1%;" on:click={goBack}>
    <i class="iconoir-arrow-left" style="font-size: 24px;"></i>
  </button>

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
