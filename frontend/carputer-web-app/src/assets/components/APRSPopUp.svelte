<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import '../styles/popups.css';
	export let show: boolean = false;
	export let aprsData: { aprsId: string; callsign: string; comment: string | null } | null = null;
	const dispatch = createEventDispatcher();
	function close() {
		dispatch('close');
	}
</script>
<main>
	{#if show && aprsData}
		<div class="popup-overlay">
			<div class="popup-container" style="min-width: 280px; width: auto; max-width: 350px;">
				<div class="popup-header">
					<h3 class="popup-title" style="margin-top: -9px;">{aprsData.callsign}</h3>
				  <button class="popup-close-btn" on:click={close} title="Close popup" style="outline: none;">
						<i class="iconoir-xmark" style="font-size: 20px; margin-top: -9px; margin-right: -9px;"></i>
					</button>
				</div>
				{#if aprsData.comment}
					<p class="popup-content">{aprsData.comment}</p>
				{:else}
					<p class="popup-content popup-content-empty">No message</p>
				{/if}
			</div>
		</div>
	{/if}
</main>