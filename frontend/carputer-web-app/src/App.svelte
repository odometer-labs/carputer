<script lang="ts">
  import { location } from 'svelte-spa-router';
  import HomeMapPage from './pages/HomeMapPage.svelte';
  import SettingPreferencePage from './pages/SettingPreferencePage.svelte';
  import WifiPage from './pages/WifiPage.svelte'
  import DashboardPage from './pages/DashboardPage.svelte';
  import MapDownloadPage from './pages/MapDownloadPage.svelte'



  // this is a list of paths that want to have the HomeMapPage 
  // in the background.
  const overlayRoutes = ['/SettingPreference',
                         '/Wifi', 
                         '/Dashboard',
                         '/MapDownload'];

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


    <!-- Wifi Page -->
  {#if $location === '/Wifi'}
    <div style="height: 100%; width: 100%;">
      <WifiPage />
    </div>
  {/if}


    <!-- Dashboard Page -->
  {#if $location === '/Dashboard'}
    <div style="height: 100%; width: 100%;">
      <DashboardPage />
    </div>
  {/if}


    <!-- Map DownLoad Page -->
  {#if $location === '/MapDownload'}
    <div style="height: 100%; width: 100%;">
      <MapDownloadPage />
    </div>
  {/if}

</main>

<style>
  main {
    font-family: Arial, sans-serif;
  }
</style>

