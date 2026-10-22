<script lang="ts">
  import { onMount } from 'svelte';
  import type { AppError } from '../../stores/errorStore';

  const AUTO_DISMISS_MS = 7000;

  let {
    error,
    onClose
  }: {
    error: AppError;
    onClose: (id: number) => void;
  } = $props();

  function getPopupLabel(appError: AppError): 'Warning' | 'Error' {
    if (appError.severity === 'vital') {
      return 'Error';
    }

    const source = (appError.source ?? '').toLowerCase();
    const message = (appError.message ?? '').toLowerCase();
    const looksLikeError =
      source.includes('error') ||
      message.includes('error') ||
      message.includes('exception') ||
      message.includes('failed');

    return looksLikeError ? 'Error' : 'Warning';
  }

  const popupLabel = $derived(getPopupLabel(error));

  onMount(() => {
    const timer = setTimeout(() => onClose(error.id), AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  });
</script>

<article class="error-popup" role="alert" aria-live="assertive">
  <div class="error-popup__header">
    <strong>{popupLabel}</strong>
    <button
      type="button"
      class="error-popup__close"
      aria-label={`Dismiss ${popupLabel.toLowerCase()}`}
      onclick={() => onClose(error.id)}
    >
      x
    </button>
  </div>

  <p class="error-popup__message">{error.message}</p>

  {#if error.source}
    <p class="error-popup__meta">Source: {error.source}</p>
  {/if}
  <p class="error-popup__meta">Time: {new Date(error.timestamp).toLocaleTimeString()}</p>
</article>

<style>
  .error-popup {
    width: 100%;
    box-sizing: border-box;
    border-radius: 12px;
    border: 1px solid #f2c66d;
    background: #fff8e9;
    color: #4a3200;
    box-shadow: 0 8px 30px rgba(55, 33, 0, 0.18);
    padding: 0.75rem 0.9rem;
  }

  .error-popup__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.3rem;
  }

  .error-popup__close {
    border: 1px solid #d8a132;
    border-radius: 6px;
    background: #ffdf9f;
    color: #4a3200;
    width: 28px;
    height: 28px;
    font-size: 16px;
    line-height: 1;
    padding: 0;
  }

  .error-popup__close:hover {
    background: #ffd68b;
  }

  .error-popup__message {
    margin: 0;
    font-size: 0.95rem;
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
  }

  .error-popup__meta {
    margin: 0.25rem 0 0;
    color: #735017;
    font-size: 0.8rem;
  }
</style>
