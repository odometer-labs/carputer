<script>
  import BackButton from "../assets/components/BackButton.svelte";

</script>


<div class="translucent-overlay">

  <!-- this is the exit buttion -->
  <BackButton />

  <!-- this is a box to show the title -->
  <div class="title-box"> 
    <h2>System Info</h2>
  </div>


  <!-- this contains both the information of the system and import/export button-->
  <div class="seperate-vert" style="height: 30%">

    <!-- this is the information of the system -->
    <div class="seperate-hori" style="height: 40%;">
      <div class="info-box">
        <h>Number of GPS Tracks: empty</h>
      </div>
      
      <div class="info-box">
        <h>Current Patch Level: empty</h>
      </div>
    </div>

    <!-- this section is for the export/import buttons -->
    <div class="seperate-hori" style="height: 75%;">
      <button>Import Track</button>

      <button>Export Track</button>
    </div>
  </div>

  <!-- this button is for checking updates of the system.-->
  <button style="margin-left: 5%;">Check for Updates</button>
  
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

  .info-box {
    display: flex;
    align-items: center;
    height: 6%;
    color: black;
    margin-bottom: 30px;
  }
  .info-box + .info-box {
    margin-top: 10%;
  }

  .seperate-vert {
    display: flex;
    justify-content: space-between;
    padding-left: 4%;
    padding-right: 4%;
    align-items: center;
  }

  .seperate-hori {
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    height: 100%;
  }

</style>
