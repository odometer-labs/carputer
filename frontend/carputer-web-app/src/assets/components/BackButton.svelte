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
  <i class="iconoir-arrow-left" style="font-size: 24px;"></i>
</button>


<style>
  .back-btn {
    position:absolute; 
    top: 2%;
    left: 1%;
  }
  
</style>