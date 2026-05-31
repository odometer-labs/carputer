<script lang="ts">
  import { onMount } from 'svelte';
  import { location } from 'svelte-spa-router';
  import { settingsPreferences } from './services/settings_preferences';
  import HomeMapPage from './pages/HomeMapPage.svelte';
  import SettingPreferencePage from './pages/SettingPreferencePage.svelte';
  import WifiPage from './pages/WifiPage.svelte';
  import SystemDataPage from './pages/SystemDataPage.svelte';
  import ErrorPage from './pages/ErrorPage.svelte';
  import ErrorPopup from './assets/components/ErrorPopup.svelte';
  import {
    appErrorState,
    clearVitalError,
    dismissNonVitalError,
    reportNonVitalError,
    reportVitalError
  } from './stores/errorStore';

  // this is a list of paths that want to have the HomeMapPage 
  // in the background.
  const overlayRoutes = ['/SettingPreference',
                         '/Wifi', 
                         '/SystemData',];

  // Checks if current route needs an overlay
  // this is reactive, includes() function returns a true or false
  $: isOverlayRoute = overlayRoutes.includes($location);

  function consoleArgsToPayload(args: unknown[]): unknown {
    if (args.length === 1) {
      return args[0];
    }

    return args
      .map((value) => {
        if (typeof value === 'string') return value;
        if (value instanceof Error) return value.stack ?? value.message;

        try {
          return JSON.stringify(value);
        } catch {
          return String(value);
        }
      })
      .join(' ');
  }

  onMount(() => {
    const originalConsoleError = console.error.bind(console);
    const originalConsoleWarn = console.warn.bind(console);

    console.error = (...args: unknown[]) => {
      originalConsoleError(...args);
      reportNonVitalError(consoleArgsToPayload(args), 'console.error');
    };

    console.warn = (...args: unknown[]) => {
      originalConsoleWarn(...args);
      reportNonVitalError(consoleArgsToPayload(args), 'console.warn');
    };

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
      console.error = originalConsoleError;
      console.warn = originalConsoleWarn;
      window.removeEventListener('error', onWindowError);
      window.removeEventListener('unhandledrejection', onUnhandledRejection);
    };
  });

  function reloadAfterVitalError(): void {
    clearVitalError();
    window.location.reload();
  }
  
  $: appBrightness = ($settingsPreferences.brightness ?? 100) / 100;
</script>

<main
  class:night-mode={$settingsPreferences.nightMode}
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
    {/if}

    <!-- Wifi Page -->
    {#if $location === '/Wifi'}
      <div style="height: 100%; width: 100%;">
        <WifiPage />
      </div>
    {/if}

    <!-- System Data Page -->
    {#if $location === '/SystemData'}
      <div style="height: 100%; width: 100%;">
        <SystemDataPage />
      </div>
    {/if}
    
  {/if}

  {#if !$appErrorState.fatalError && $appErrorState.notifications.length > 0}
    <div class="warning-popup-stack" aria-live="polite" aria-label="Application warnings">
      {#each $appErrorState.notifications as notification, i (notification.id)}
        {@const depth = $appErrorState.notifications.length - 1 - i}
        {#if depth < 3}
          <div
            class="popup-layer"
            style="--depth: {depth}; z-index: {2500 - depth};"
          >
            <ErrorPopup error={notification} onClose={dismissNonVitalError} />
          </div>
        {/if}
      {/each}
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
    bottom: 0.9rem;
    left: 0.9rem;
    right: 0.9rem;
    width: auto;
    max-width: 420px;
    margin-left: auto;
    box-sizing: border-box;
    z-index: 2500;
    display: grid;
    pointer-events: none;
  }

  /* All layers sit in the same grid cell so they physically overlap */
  .popup-layer {
    grid-row: 1;
    grid-column: 1;
    width: 100%;
    align-self: end;
    pointer-events: none;
    transform:
      translateY(calc(var(--depth, 0) * -8px))
      scale(calc(1 - var(--depth, 0) * 0.04));
    transform-origin: bottom center;
    opacity: calc(1 - var(--depth, 0) * 0.12);
    transition: transform 0.25s ease, opacity 0.25s ease;
  }

  .popup-layer :global(article) {
    pointer-events: auto;
  }
</style>

