<script lang="ts">
  //import { systemInfo } from "some place that catches information from backend"


  // delete this after the indicators are implemented with backend information.
  let speedMPH = 20;

</script>



<div class="speed">
  <p style="text-align: center;">
    <strong style="font-size:30px;">{speedMPH}</strong><br>
    MPH
  </p>
</div>



<style>
  .speed {
    right: 25px;
    bottom: 35px;
    position: absolute;
    z-index: 1000;

    width: 100px;
    height: 80px;
    padding: 0px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border: 1px solid white;
    border-radius: 20%;
    background-color: rgba(188, 188, 188, 0.9);
    color: #333;
    font-weight: 500;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    transition: all 0.2s;
    outline: none;
  }

</style>