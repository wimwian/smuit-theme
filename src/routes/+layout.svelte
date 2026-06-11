<!--
  Copyright (c) 2026 @wimwian
  SPDX-License-Identifier: MIT
-->
<script lang="ts">
	import './layout.css';
	import { ThemeToggle } from '$lib/index.js';
	import { initTheme } from '$lib/theme.js';

	const { children } = $props();

	$effect(() => {
		initTheme();
	});
</script>

<header class="app-header">
	<span class="app-header-name">smuit-theme</span>
	<ThemeToggle />
</header>

{@render children()}
