<script lang="ts">
  import type { AppError } from '../../stores/errorStore';

  let {
    error,
    onClose
  }: {
    error: AppError;
    onClose: (id: number) => void;
  } = $props();
</script>

<article class="error-popup" role="alert" aria-live="assertive">
  <div class="error-popup__header">
    <strong>Warning</strong>
    <button
      type="button"
      class="error-popup__close"
      aria-label="Dismiss warning"
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
    width: min(420px, calc(100vw - 2rem));
    border-radius: 12px;
    border: 1px solid #f2c66d;
    background: #fff8e9;
    color: #4a3200;
    box-shadow: 0 8px 30px rgba(55, 33, 0, 0.18);
    padding: 0.75rem 0.9rem;
    bottom: 0.5%;
    position: fixed;
    right: 2%;
    transform: translateX(2%);
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
