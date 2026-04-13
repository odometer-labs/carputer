<script>
  import BackButton from "../assets/components/BackButton.svelte";
  import SystemIndicators from "../assets/components/SystemIndicators.svelte";
  import download_icon from  "../assets/download-bold.svg";

</script>


<div class="translucent-overlay">
    


  <!-- this is a box to show the title -->
  <div class="title-box">   
    <!-- this is the exit buttion -->
    <BackButton />
    <h2>Maps</h2>

    <SystemIndicators 
      isActiveBackground={false} 
      isRoadDiscoverActive={false}
    />
  </div>

  <!-- for now it's just a button to download the map-->
  <button class=download-map-btn>
    <img src={download_icon} alt="Download" class="icons" />
    Download Map
  </button>

</div>


<style>
  .download-map-btn {
    position:relative; 
    margin-top: 5%; 
    left: 5%;
  
    background-color: rgba(188, 188, 188);
    color: black;

    border: none;
    outline: none;

    display: flex;
    align-items: center;

    justify-content: center;
  }
  .download-map-btn:hover {
    background-color: rgba(202, 202, 202);
    box-shadow: none;
  }
  
  .icons {
    width: 20px;
    height: 20px;
    margin-right: 4px;
  }

</style>
