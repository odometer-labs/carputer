<script lang="ts">
  import type { AppError } from '../stores/errorStore';

  let {
    error,
    onReload
  }: {
    error: AppError;
    onReload: () => void;
  } = $props();
</script>

<section class="fatal-error-page" role="alert" aria-live="assertive">
  <h1>System Error</h1>
  <p class="fatal-error-page__message">
    The app hit a vital runtime error and cannot continue safely. Check the web remote interface to see more logs.
  </p>

  <p class="fatal-error-page__detail"><strong>Message:</strong> {error.message}</p>
  {#if error.source}
    <p class="fatal-error-page__detail"><strong>Source:</strong> {error.source}</p>
  {/if}
  <p class="fatal-error-page__detail"><strong>Time:</strong> {new Date(error.timestamp).toLocaleString()}</p>

  <button type="button" class="fatal-error-page__btn" onclick={onReload}>
    Reload App
  </button>
</section>

<style>
  .fatal-error-page {
    min-height: 100vh;
    width: 100%;
    background: linear-gradient(145deg, #fce4e4, #fff4f4 45%, #f6e2e2);
    color: #320000;
    padding: 2rem 1.25rem;
    box-sizing: border-box;
  }

  h1 {
    margin-top: 0;
    margin-bottom: 0.5rem;
  }

  .fatal-error-page__message {
    margin-top: 0;
    margin-bottom: 1.25rem;
    font-size: 1rem;
  }

  .fatal-error-page__detail {
    margin: 0.4rem 0;
    font-size: 0.95rem;
    word-break: break-word;
  }

  .fatal-error-page__btn {
    display: block;
    margin-top: 1.5rem;
    border: 1px solid #7a1f1f;
    border-radius: 10px;
    background: #b12525;
    color: #fff;
    font-weight: 600;
    padding: 0.65em 1.4em;
  }

  .fatal-error-page__btn:hover {
    background: #9a1e1e;
  }
</style>
