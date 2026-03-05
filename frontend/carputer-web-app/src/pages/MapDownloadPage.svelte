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
  
    background-color: rgba(188, 188, 188, 0.9);
    color: black;

    border: none;
    outline: none;

    display: flex;
    align-items: center;

    justify-content: center;
  }
  .download-map-btn:hover {
    background-color: rgba(202, 202, 202, 0.9);
    box-shadow: none;
  }

</style>
