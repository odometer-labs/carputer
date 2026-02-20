<script>
  import { location } from 'svelte-spa-router';
  import HomeMapPage from './pages/HomeMapPage.svelte';
  import ExamplePage from './pages/ExamplePage.svelte';
  

</script>


<main style="margin: 0; padding: 0; height: 100%; width: 100%;">
  
  <!-- Keep all pages mounted, control visibility with CSS -->
  <div style:display={$location === '/' ? 'block' : 'none'} style="height: 100%; width: 100%;">
    <HomeMapPage />
  </div>
  
  <div style:display={$location === '/other' ? 'block' : 'none'} style="height: 100%; width: 100%;">
    <ExamplePage />
  </div>

</main>

<style>
  main {
    font-family: Arial, sans-serif;
  }
</style>

