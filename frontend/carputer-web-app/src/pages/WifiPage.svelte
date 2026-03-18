<script>
  import BackButton from "../assets/components/BackButton.svelte";
  

  // this is for if the user wishes to turn off the wifi
  let isWifiOn = true;

  // text to let the user know if the switch is on or off.
  let wifiStatus = "ON"
  // Reactive statement
  $: wifiStatus = isWifiOn ? "ON" : "OFF";

</script>


<div class="translucent-overlay">



  
  <div class="title-box">
    <!-- this is the exit buttion -->
    <BackButton />
    <h2>Wifi</h2>
  </div>

  <!-- This button is to disable the wifi -->
  <div class="switch-box">
    <label class="switch">
      <input type="checkbox" bind:checked={isWifiOn} />
      
      <!-- Icon changes based on state -->
      <i class={isWifiOn ? "iconoir-switch-on" : "iconoir-switch-off"}></i>

    </label>

    <h3 class={isWifiOn ? "wifi_text_on" : "wifi_text_off"}>{wifiStatus}</h3>
  </div>


  <!-- this is just a box to tell the user that below
      is the current connection                       -->
  <div class="option-box">
    <h3>Currently Connected To:</h3>
  </div>
  
  <!-- this is just a box to tell the user that below
      is the aviable connections                    -->
  <div class="option-box" style="margin-top: 10%;">
    <h3>Other Networks:</h3>
  </div>

</div>


<style>
  .option-box {
    display: flex;
    border-bottom: 1px solid rgba(0, 0, 0, 0.5);
    padding-left: 5%;
    padding-right: 5%;
    color: black;
  }

  .wifi_text_on {
    color: rgb(33, 140, 0);
    font-size: 18px;
    margin-left: 5%;
  }
  .wifi_text_off {
    color: rgb(180, 42, 0);
    font-size: 18px;
    margin-left: 5%;
  } 
  .switch {
    cursor: pointer;
    color: #333;

    display: inline-block;
    cursor: pointer;
  }

  .switch input {
    display: none; 
  }

  .switch i {
    font-size: 64px;
    display: inline-block;
    cursor: pointer;
  }

  .switch-box {
    position: absolute;
    top: 1%;
    right: 0%;
    display: grid;
    grid-template-columns: repeat(2, 1fr); 
    gap: 10px;
  }
    
</style>
