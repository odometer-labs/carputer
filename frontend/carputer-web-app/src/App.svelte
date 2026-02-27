<script lang="ts">
  import { location } from 'svelte-spa-router';
  import HomeMapPage from './pages/HomeMapPage.svelte';
  import SettingPreferencePage from './pages/SettingPreferencePage.svelte';


  // this is a list of paths that want to have the HomeMapPage 
  // in the background.
  const overlayRoutes = ['/SettingPreference', '/Wifi', '/DownloadTrack'];

  // Checks if current route needs an overlay
  // this is reactive, includes() function returns a true or false
  $: isOverlayRoute = overlayRoutes.includes($location);

</script>

<main style="margin: 0; padding: 0; height: 100%; width: 100%;">
  
  <!-- Pages are continuously mounted, visibility controlled by CSS. -->
   
  <div style:display={$location === '/' || isOverlayRoute ? 'block' : 'none'} style="height: 100%; width: 100%;">
    <HomeMapPage />
  </div>


    <!-- Settings and Preferences page -->
  {#if $location === '/SettingPreference'}
    <div style="height: 100%; width: 100%;">
      <SettingPreferencePage />
    </div>
  {/if}

</main>

<style>
  main {
    font-family: Arial, sans-serif;
  }
</style>

