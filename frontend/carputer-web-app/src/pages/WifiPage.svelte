<script>
  import { push } from 'svelte-spa-router';

  
  // Function to navigate back to the home map page
  function goBack() {
    push('/');
  }

  // this is for if the user wishes to turn off the wifi
  let isWiFiOn = true;

</script>


<div class="translucent-overlay">

  <!-- this is the exit buttion -->
  <!-- svelte-ignore a11y_consider_explicit_label -->
  <button style="position:absolute; top:2%; left:1%;" on:click={goBack}>
    <i class="iconoir-arrow-left" style="font-size: 24px;"></i>
  </button>
  
  <div class="title-box">
    <h2>Wifi</h2>
  </div>

  <!-- This button is to disable the wifi -->
  <label class="switch">
    <input type="checkbox" bind:checked={isWiFiOn} />
    
    <!-- Icon changes based on state -->
    <i class={isWiFiOn ? "iconoir-switch-on" : "iconoir-switch-off"}></i>

  </label>


  <!-- this is just a box to tell the user that below
      is the current connection                       -->
  <div class="option-box">
    <h3>currently Connected To:</h3>
  </div>
  
  <!-- this is just a box to tell the user that below
      is the aviable connections                    -->
  <div class="option-box" style="margin-top: 10%;">
    <h3>Other Networks:</h3>
  </div>

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
    border: 2px solid rgba(0, 0, 0, 1);
    text-align: center;
    color: rgb(0, 0, 0);
  }

  .option-box {
    display: flex;
    border-bottom: 1px solid rgba(0, 0, 0, 0.5);
    padding-left: 5%;
    padding-right: 5%;
    color: black;
  }

  .switch {
    position: absolute;
    cursor: pointer;
    top: 1%;
    right: 3%;
  }

  .switch input {
    display: none; 
  }

  .switch i {
    font-size: 64px;
  }
    
</style>
