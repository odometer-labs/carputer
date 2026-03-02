<script>
  import { push } from 'svelte-spa-router';

  
  // Function to navigate back to the home map page
  function goBack() {
    push('/');
  }

</script>


<div class="translucent-overlay">

    <!-- this is a box to show the title -->
    <div class="title-box"> 

        <!-- this is the exit buttion -->
        <button on:click={goBack}>Return</button>
        
        <h2>Wifi</h2>

        <!-- This button is to disable the wifi -->
        <input type="checkbox" style="transform: scale(3);"/>

    </div>

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
    color: rgb(0, 0, 0);

    display: flex;
    justify-content: space-between;
    padding-left: 1%;
    padding-right: 3%;
    align-items: center;
  }

  .option-box {
    display: flex;
    border-bottom: 1px solid rgba(0, 0, 0, 0.5);
    padding-left: 5%;
    padding-right: 5%;
    color: black;
  }
</style>
