<script lang="ts">
  import { onMount } from 'svelte';
  import { location } from 'svelte-spa-router';
  import { preferences } from './services/preferences';
  import HomeMapPage from './pages/HomeMapPage.svelte';
  import SettingPreferencePage from './pages/SettingPreferencePage.svelte';
  import WifiPage from './pages/WifiPage.svelte';
  import DashboardPage from './pages/DashboardPage.svelte';
  import MapDownloadPage from './pages/MapDownloadPage.svelte';
  import ErrorPage from './pages/ErrorPage.svelte';
  import ErrorPopup from './assets/components/ErrorPopup.svelte';
  import {
    appErrorState,
    clearVitalError,
    dismissNonVitalError,
    reportNonVitalError,
    reportVitalError
  } from './stores/errorStore';
  import type { AppError } from './stores/errorStore';

  // this is a list of paths that want to have the HomeMapPage 
  // in the background.
  const overlayRoutes = ['/SettingPreference',
                         '/Wifi', 
                         '/Dashboard',
                         '/MapDownload'];

  // Checks if current route needs an overlay
  // this is reactive, includes() function returns a true or false
  $: isOverlayRoute = overlayRoutes.includes($location);

  let nextWarning: AppError | null = null;
  $: nextWarning = $appErrorState.notifications[0] ?? null;

  onMount(() => {
    const onWindowError = (event: ErrorEvent): void => {
      const errorValue = event.error ?? event.message;
      reportVitalError(errorValue, 'window.error');
    };

    const onUnhandledRejection = (event: PromiseRejectionEvent): void => {
      reportNonVitalError(event.reason, 'window.unhandledrejection');
    };

    window.addEventListener('error', onWindowError);
    window.addEventListener('unhandledrejection', onUnhandledRejection);

    return () => {
      window.removeEventListener('error', onWindowError);
      window.removeEventListener('unhandledrejection', onUnhandledRejection);
    };
  });

  function reloadAfterVitalError(): void {
    clearVitalError();
    window.location.reload();
  }
  $: appBrightness = ($preferences.brightness ?? 100) / 100;
</script>

<main
  class:night-mode={$preferences.nightMode}
  class="app-shell"
  style={`margin: 0; padding: 0; height: 100%; width: 100%; --app-brightness: ${appBrightness};`}
>
  {#if $appErrorState.fatalError}
    <ErrorPage error={$appErrorState.fatalError} onReload={reloadAfterVitalError} />
  {:else}
  
  <!-- Pages are continuously mounted, visibility controlled by CSS. -->
   
  <div style:display={$location === '/' || isOverlayRoute ? 'block' : 'none'} style="height: 100%; width: 100%;">
    <HomeMapPage />
  </div>


    <!-- Settings and Preferences page -->
  {#if $location === '/SettingPreference'}
    <div style="height: 100%; width: 100%;">
      <SettingPreferencePage />
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
  {/if}

  {#if !$appErrorState.fatalError}
    <div class="warning-popup-stack" aria-live="polite" aria-label="Application warnings">
      {#if nextWarning}
        <ErrorPopup error={nextWarning} onClose={dismissNonVitalError} />
      {/if}
    </div>
  {/if}

</main>

<style>
  .app-shell {
    font-family: Arial, sans-serif;
    background: #ffffff;
    filter: brightness(var(--app-brightness, 1));
    transition: filter 0.2s ease, background-color 0.2s ease;
  }

  .app-shell.night-mode {
    background: #111111;
    filter: invert(1) hue-rotate(180deg) brightness(var(--app-brightness, 1));
  }

  .warning-popup-stack {
    position: fixed;
    top: 0.9rem;
    right: 0.9rem;
    z-index: 2500;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
    align-items: flex-end;
    pointer-events: none;
  }

  .warning-popup-stack :global(article) {
    pointer-events: auto;
  }
</style>

