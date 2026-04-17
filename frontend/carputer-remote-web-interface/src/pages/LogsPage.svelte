<script lang="ts">
  import { push } from 'svelte-spa-router';
  import AppBar from '../assets/components/AppBar.svelte';
</script>

<main class="logs-shell">
  <AppBar title="Logs" />
</main>

<style>
  .logs-shell {
    width: 100%;
    min-height: 100%;
    background: var(--surface-color, #eeeeee);
    color: var(--text-color, #111111);
  }
</style>