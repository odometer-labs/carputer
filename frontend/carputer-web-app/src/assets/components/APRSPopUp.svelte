<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	export let show: boolean = false;
	export let aprsData: { aprsId: string; callsign: string; comment: string | null } | null = null;
	const dispatch = createEventDispatcher();
	function close() {
		dispatch('close');
	}
</script>
<main>
	{#if show && aprsData}
		<div class="aprs-popup">
			<div class="aprs-popup-header">
				<span class="aprs-popup-callsign">{aprsData.callsign}</span>
				<button class="aprs-popup-close" on:click={close}>
					<i class="iconoir-xmark" style="font-size: 16px;"></i>
				</button>
			</div>
			{#if aprsData.comment}
				<p class="aprs-popup-comment">{aprsData.comment}</p>
			{:else}
				<p class="aprs-popup-comment aprs-popup-no-comment">No message</p>
			{/if}
		</div>
	{/if}
</main>
<style>
	.aprs-popup {
		position: absolute;
		left: 50%;
		top: 20%;
		transform: translate(-50%, 0);
		background: white;
		border-radius: 10px;
		box-shadow: 0 4px 14px rgba(0,0,0,0.3);
		padding: 18px 24px;
		min-width: 220px;
		z-index: 2100;
	}
	.aprs-popup-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 8px;
	}
	.aprs-popup-callsign {
		font-weight: bold;
		font-size: 1.1rem;
	}
	.aprs-popup-close {
		background: none;
		border: none;
		cursor: pointer;
		padding: 2px 6px;
		border-radius: 4px;
		transition: background 0.2s;
	}
	.aprs-popup-close:hover {
		background: #eee;
	}
	.aprs-popup-comment {
		margin: 0;
		color: #222;
		font-size: 1rem;
	}
	.aprs-popup-no-comment {
		color: #888;
		font-style: italic;
	}
</style>