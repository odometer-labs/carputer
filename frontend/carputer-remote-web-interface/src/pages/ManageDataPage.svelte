<script lang="ts">
  import BackButton from '../assets/components/BackButton.svelte';
</script>

<main class="manage-data-shell">
  <header class="app-bar">
    <BackButton />
    <h1>Manage Data</h1>
  </header>
</main>

<style>
  .manage-data-shell {
    width: 100%;
    min-height: 100%;
    background: var(--surface-color, #eeeeee);
    color: var(--text-color, #111111);
  }

  .app-bar {
    position: sticky;
    top: 0;
    display: flex;
    align-items: center;
    gap: 1rem;
    min-height: 64px;
    padding: 0 1rem;
    background-color: var(--primary-color, rgba(188, 188, 188, 0.9));
    border-top: 2px solid #000000;
    border-bottom: 2px solid #000000;
  }

  .app-bar h1 {
    margin: 0;
    font-size: 1.5rem;
  }
</style>