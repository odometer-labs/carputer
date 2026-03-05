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
  .download-map-btn {
    position:relative; 
    margin-top: 5%; 
    left: 5%;
  
    background-color: var(--primary-color);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);

    border: 1px solid white;
    outline: none;

    display: flex;
    align-items: center;

    justify-content: center;
  }
  .download-map-btn:hover {
    background-color: var(--secondary-color);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
  }

</style>
