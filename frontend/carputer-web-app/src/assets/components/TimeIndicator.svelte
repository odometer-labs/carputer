<script lang="ts">
  //TODO : for now the time indicator will be this, but in the furture we might need
  // to make a store for time. Since that is one of the requirements (to be able to change
  // time zones or change time manually.)

  import { onMount } from "svelte";
  import { formatTime } from "../../utils/timeFormatter";//formats time data

  let time = new Date();
  let hoursMinutes = formatTime(time);

  onMount(()=>{
    const interval = setInterval(()=>{
      time = new Date();
      hoursMinutes = formatTime(time);
    }, 1000 );

    return() => clearInterval(interval)
  });


</script>


<!--shows what the time is-->
<div class="indicator">
    <strong>{hoursMinutes}</strong>
</div>



<style>
  .indicator {
    gap: 5px;
    width: 70px;
  }

</style>