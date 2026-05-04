<script>
  import arrow from "../icons/arrow-left-bold.svg";
  import { goBack } from "../../utils/navigation";
</script>

<!-- this is the exit button -->
<!-- svelte-ignore a11y_consider_explicit_label -->
<button class="back-btn" on:click={goBack}>
  <img src={arrow} alt="Back" style="width:48px; height:48px;" />
</button>


<style>
  .back-btn {
    background-color: rgba(227, 227, 227, 0.9);
    position:absolute; 
    left: 1%;

    width: 50px;
    height: 50px;

    border-radius: 50%;
    outline: none;

    display: flex;
    align-items: center;

    justify-content: center;

    border: none;
  }
  .back-btn:hover {
    background-color: rgb(241, 241, 241);
  }
  
</style>