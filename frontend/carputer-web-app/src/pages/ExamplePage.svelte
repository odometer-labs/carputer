<!-- DELETE ME -->
<!-- This is an example page to demonstrate page navigation. 
Once you understand how to navigate between pages, you can delete this file. -->

<script>
  import { push } from 'svelte-spa-router';

  // Function to navigate back to the home map page
  function goBack() {
    push('/');
  }

</script>

<div style="padding: 20px;">
  <h1>Some Other Page</h1>
  <p>This is another page in the application.</p>
  <button on:click={goBack}>Go Back</button>
</div>