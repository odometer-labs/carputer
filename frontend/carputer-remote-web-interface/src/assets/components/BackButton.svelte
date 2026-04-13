<script>
  import arrow from "../icons/arrow-left-bold.svg";
  import { goBack } from "../../utils/navigation";
</script>

<button class="back-btn" on:click={goBack}>
  Back
</button>


<style>
  .back-btn {
    border: 1px solid #ffffff;
    border-radius: 6px;
    background-color: var(--secondary-color, rgb(225, 225, 225));
    color: #222222;
    padding: 0.5rem 0.75rem;
    cursor: pointer;
    font: inherit;
  }
  
</style>