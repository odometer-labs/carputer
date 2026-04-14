
<script>
  import BackButton from './BackButton.svelte';
  let { title } = $props();
</script>

<header class="app-bar">
  <BackButton />
  <h1 style="display: flex; justify-content: center; flex: 1;">{title}</h1>
</header>

<style>
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
    z-index: 10;
  }
  
  .app-bar h1 {
    margin: 0;
    font-size: 1.5rem;
  }
</style>