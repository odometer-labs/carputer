<script lang="ts">
  import AppBar from '../assets/components/AppBar.svelte';
</script>

<main class="manage-data-shell">
  <AppBar title="Data Manager" />
</main>

<style>
  .manage-data-shell {
    width: 100%;
    min-height: 100%;
    background: var(--surface-color, #eeeeee);
    color: var(--text-color, #111111);
  }
</style>