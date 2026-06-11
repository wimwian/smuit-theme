<!--
  Copyright (c) 2026 @wimwian
  SPDX-License-Identifier: MIT
-->
<script lang="ts">
	import { getTheme, setTheme, type Theme } from './theme.js';
	import './ThemeToggle.css';

	interface Props {
		/** Extra classes to merge onto the button. */
		class?: string;
	}

	let { class: className }: Props = $props();

	// Local mirror of the global `data-theme` register; synced on mount.
	let theme = $state<Theme>('light');

	$effect(() => {
		theme = getTheme();
	});

	function toggle() {
		theme = theme === 'dark' ? 'light' : 'dark';
		setTheme(theme);
	}
</script>

<button
	type="button"
	class={['theme-toggle', className]}
	onclick={toggle}
	aria-label="Toggle color theme"
	aria-pressed={theme === 'dark'}
	title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
>
	{#if theme === 'dark'}
		<!-- Moon: shown in dark mode, click switches to light -->
		<svg
			class="theme-toggle-icon"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
			aria-hidden="true"
		>
			<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
		</svg>
	{:else}
		<!-- Sun: shown in light mode, click switches to dark -->
		<svg
			class="theme-toggle-icon"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
			aria-hidden="true"
		>
			<circle cx="12" cy="12" r="4" />
			<path
				d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"
			/>
		</svg>
	{/if}
</button>
