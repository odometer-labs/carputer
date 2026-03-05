<script>
  import { push } from 'svelte-spa-router';

  
  // Function to navigate back to the home map page
  function goBack() {
    push('/');
  }

</script>


<!-- this is the exit buttion -->
<!-- svelte-ignore a11y_consider_explicit_label -->
<button class="back-btn" on:click={goBack}>
  <i class="iconoir-arrow-left"></i>
</button>


<style>
  .back-btn {
    background-color: var(--secondary-color);
    position:absolute; 
    top: 1.5%;
    left: 1%;

    width: 50px;
    height: 50px;

    border-radius: 50%;
    border: 1px solid white;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    outline: none;

    display: flex;
    align-items: center;

    justify-content: center;
  }
  .back-btn:hover {
    background-color: rgb(241, 241, 241);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
  }
  
</style>