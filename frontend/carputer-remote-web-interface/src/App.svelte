<script lang="ts">
  import { router } from 'svelte-spa-router';
  import HomePage from './pages/HomePage.svelte';
  import ManageDataPage from './pages/ManageDataPage.svelte';
  import TracksPage from './pages/TracksPage.svelte';
</script>

<main
  class="app-shell"
  style="margin: 0; padding: 0; height: 100%; width: 100%;"
>
  {#if router.location === '/' || router.location === ''}
    <div style="height: 100%; width: 100%;">
      <HomePage />
    </div>
  {/if}

  {#if router.location === '/Tracks'}
    <div style="height: 100%; width: 100%;">
      <TracksPage />
    </div>
  {/if}

  {#if router.location === '/ManageData'}
    <div style="height: 100%; width: 100%;">
      <ManageDataPage />
    </div>
  {/if}

</main>

<style>
  .app-shell {
    font-family: Arial, sans-serif;
    background: #ffffff;
  }

</style>
