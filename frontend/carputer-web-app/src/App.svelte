<script>
  import { location } from 'svelte-spa-router';
  import HomeMapPage from './pages/HomeMapPage.svelte';

</script>


<main style="margin: 0; padding: 0; height: 100%; width: 100%;">
  
  <!-- Pages are continuously mounted, visibility controlled by CSS. -->
   
  <div style:display={$location === '/' ? 'block' : 'none'} style="height: 100%; width: 100%;">
    <HomeMapPage />
  </div>

</main>

<style>
  main {
    font-family: Arial, sans-serif;
  }
</style>

