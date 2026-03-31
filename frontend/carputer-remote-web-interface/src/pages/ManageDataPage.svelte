<script lang="ts">
  import { push } from 'svelte-spa-router';

  function goBack(): void {
    push('/');
  }
</script>

<main class="manage-data-shell">
  <header class="app-bar">
    <button class="back-btn" type="button" onclick={goBack}>Back</button>
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

  .back-btn {
    border: 1px solid #ffffff;
    border-radius: 6px;
    background-color: var(--secondary-color, rgb(225, 225, 225));
    color: #222222;
    padding: 0.5rem 0.75rem;
    cursor: pointer;
    font: inherit;
  }
</style>