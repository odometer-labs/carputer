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
      <button class="button-color">Import Track</button>

      <button class="button-color">Export Track</button>
    </div>
  </div>

  <!-- this button is for checking updates of the system.-->
  <button class="button-color" style="margin-left: 5%;">Check for Updates</button>
  
</div>


<style>
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

  .button-color {
    background-color: rgba(188, 188, 188, 0.9);

    color: black;

    outline: none;

    display: flex;
    align-items: center;

    justify-content: center;
    border: none;
  }
  .button-color:hover {
    background-color: rgba(202, 202, 202, 0.9);
  }

</style>
