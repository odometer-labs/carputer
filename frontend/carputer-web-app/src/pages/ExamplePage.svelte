<script>
  import { push } from 'svelte-spa-router';

  function goBack() {
    push('/');
  }

</script>

<div style="padding: 20px;">
  <h1>Some Other Page</h1>
  <p>This is another page in the application.</p>
  <button on:click={goBack}>Go Back</button>
</div>