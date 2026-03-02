<script>
  import { push } from 'svelte-spa-router';

  
  // Function to navigate back to the home map page
  function goBack() {
    push('/');
  }

</script>


<div class="translucent-overlay">

    <!-- this is the exit buttion -->
    <button style="position:absolute; top:2%; left:1%;" on:click={goBack}>Return</button>

    <!-- this contains everything for settins -->
    <div>
        <!-- this is a box to show the title -->
        <div class="title-box"> 
            <h2>Settings</h2>
        </div>

        <!-- the box contains a settings functionality 
            THIS IS ALL JUST TEMPORARY, I JUST DIDN'T WANT THIS PAGE
            TO BE EMPY                                              -->
        <div class="option-box">
            <h3>Togle something</h3>
            <input type="checkbox" style="margin-left: auto;"/>
        </div>
        
        <div class="option-box">
            <h3>Miles to Discover Roads</h3>
            <input type="range" min="1" max="100" value="50" style="margin-left: auto;">
        </div>
    </div>


    <!-- this contains everything for settins -->
    <div>
        <!-- This page will also have a Preferences title -->
        <div class="title-box" style="margin-top: 10%;"> 
            <h2>Preferences</h2>
        </div>

        <!-- the box contains a preferences functionality
            THIS IS ALL JUST TEMPORARY, I JUST DIDN'T WANT THIS PAGE
            TO BE EMPY                                              -->
        <div class="option-box">
            <h3>Night Mode</h3>
            <input type="checkbox" style="margin-left: auto;"/>
        </div>
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
    text-align: center;
    border: 2px solid rgba(0, 0, 0, 1);
    color: rgb(0, 0, 0);
  }

  .option-box {
    display: flex;
    border: 1px solid rgba(0, 0, 0, 0.5);
    padding-left: 5%;
    padding-right: 5%;
    color: black;
  }
</style>
