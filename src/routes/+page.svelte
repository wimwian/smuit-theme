<!--
  Copyright (c) 2026 @wimwian
  SPDX-License-Identifier: MIT
-->
<script lang="ts">
	// ── Hue model ──────────────────────────────────────────────────────────────
	// Token sets mirror what smuit-theme-generator emits into output.css:
	//   neutral + primary/secondary/tertiary → full surface set (incl. hover/focus)
	//   error/warning/success (RAG)           → reduced set (no hover/focus)
	type Hue = { name: string; infix: string; parts: string[] };

	const FULL = ['bg', 'bg-hover', 'bg-focus', 'fg', 'border', 'border-bold'];
	const RAG = ['bg', 'fg', 'border', 'border-bold'];

	const HUES: Hue[] = [
		{ name: 'neutral', infix: '', parts: FULL },
		{ name: 'primary', infix: 'primary', parts: FULL },
		{ name: 'secondary', infix: 'secondary', parts: FULL },
		{ name: 'tertiary', infix: 'tertiary', parts: FULL },
		{ name: 'error', infix: 'error', parts: RAG },
		{ name: 'warning', infix: 'warning', parts: RAG },
		{ name: 'success', infix: 'success', parts: RAG }
	];

	const TABS = [...HUES.map((h) => h.name), 'typography', 'elevation', 'login'];

	const ELEVATIONS = ['none', '2xs', 'xs', 'sm', 'md', 'lg', 'xl', '2xl'];

	let active = $state<string>(TABS[0]);
	const activeHue = $derived(HUES.find((h) => h.name === active));

	// Typography sub-tabs: which surface register the samples render on.
	const TYPE_SURFACES = ['neutral', 'primary', 'secondary', 'tertiary'];
	let typeSurfaceName = $state<string>('neutral');
	const typeSurface = $derived(HUES.find((h) => h.name === typeSurfaceName)!);

	function tok(h: Hue, part: string): string {
		return h.infix ? `--surface-${h.infix}-${part}` : `--surface-${part}`;
	}
	const cssVar = (name: string) => `var(${name})`;

	// ── Typography model ─────────────────────────────────────────────────────────
	// Only cls + role are declared; the numeric metrics (size/line-height/weight/
	// width) are read from the rendered @utility CSS at runtime, so they can never
	// drift from what smuit-theme-generator emits.
	type Type = { cls: string; role: string };
	type Metrics = { size: number; lh: number; wt: number; wd: number };

	const TYPE: Type[] = [
		{ cls: 'display-sm', role: 'display' },
		{ cls: 'display-md', role: 'display' },
		{ cls: 'display-lg', role: 'display' },
		{ cls: 'title-sm', role: 'title' },
		{ cls: 'title-md', role: 'title' },
		{ cls: 'title-lg', role: 'title' },
		{ cls: 'heading-xs', role: 'heading' },
		{ cls: 'heading-sm', role: 'heading' },
		{ cls: 'heading-md', role: 'heading' },
		{ cls: 'heading-lg', role: 'heading' },
		{ cls: 'heading-xl', role: 'heading' },
		{ cls: 'body-xs', role: 'body' },
		{ cls: 'body-sm', role: 'body' },
		{ cls: 'body-md', role: 'body' },
		{ cls: 'body-lg', role: 'body' },
		{ cls: 'body-xl', role: 'body' },
		{ cls: 'label-sm', role: 'label' },
		{ cls: 'label-md', role: 'label' },
		{ cls: 'label-lg', role: 'label' },
		{ cls: 'code-sm', role: 'code' },
		{ cls: 'code-md', role: 'code' },
		{ cls: 'code-lg', role: 'code' }
	];

	// Populated in the measurement effect from getComputedStyle on each utility.
	let typeMetrics = $state<Record<string, Metrics>>({});

	// Sample copy: two lorem paragraphs by default; headings/titles show one line.
	const LINE = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.';
	const PARA1 =
		'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.';
	const PARA2 =
		'Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.';

	const CODE = 'function greet(name) {\n  console.log(`Hello, ${name}!`);\n}';

	const DISPLAY = 'Lorem ipsum dolor sit';

	const oneLine = (t: Type) => t.role === 'heading' || t.role === 'title';
	const isCode = (t: Type) => t.role === 'code';
	const isDisplay = (t: Type) => t.role === 'display';

	// WCAG AAA: 7:1 for normal text, 4.5:1 for large text (≥24px, or ≥18.66px bold).
	const AAA_NORMAL = 7;
	const AAA_LARGE = 4.5;
	function aaaThreshold(m: Metrics | undefined): number {
		if (!m) return AAA_NORMAL;
		const large = m.size >= 24 || (m.size >= 18.66 && m.wt >= 700);
		return large ? AAA_LARGE : AAA_NORMAL;
	}

	// ── Contrast measurement ─────────────────────────────────────────────────────
	// Resolve each surface bg/fg to sRGB and compute the WCAG ratio, for both
	// theme registers. We flip the document's data-theme synchronously so each
	// register resolves correctly even if the page is currently toggled — no paint
	// happens between the writes, so there's no visible flicker.
	type Pair = { light: number; dark: number };
	type Rgb = [number, number, number];
	type SurfaceColors = { bg: string; fg: string; border: string };

	let contrasts = $state<Record<string, Pair>>({});
	// Concrete light-register colors captured during measurement, so the typography
	// "light" column stays light regardless of the page toggle — no hardcoding.
	let lightColors = $state<Record<string, SurfaceColors>>({});

	function resolve(probe: HTMLElement, cssValue: string): string {
		probe.style.color = cssValue;
		return getComputedStyle(probe).color; // var(...) → concrete color
	}
	function toRgb(ctx: CanvasRenderingContext2D, color: string): Rgb {
		ctx.fillStyle = '#000';
		ctx.fillStyle = color; // canvas normalises any CSS color → sRGB bytes
		ctx.fillRect(0, 0, 1, 1);
		const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
		return [r, g, b];
	}

	function relLuminance([r, g, b]: [number, number, number]): number {
		const lin = (c: number) => {
			const s = c / 255;
			return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
		};
		return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
	}

	function ratio(a: [number, number, number], b: [number, number, number]): number {
		const la = relLuminance(a);
		const lb = relLuminance(b);
		const hi = Math.max(la, lb);
		const lo = Math.min(la, lb);
		return (hi + 0.05) / (lo + 0.05);
	}

	// Read type metrics from the authored @utility rules. getComputedStyle can't be
	// used for width: this engine doesn't map `font-width` (the name the generator
	// emits) onto computed `font-stretch`. Reading the rule's declared value works
	// regardless, and stays in lock-step with whatever the generator produces.
	function readUtilityMetrics(): Record<string, Metrics> {
		const want = new Set(TYPE.map((t) => t.cls));
		const out: Record<string, Metrics> = {};
		const visit = (rules: CSSRuleList) => {
			for (const rule of Array.from(rules)) {
				if (rule instanceof CSSStyleRule) {
					const cls = rule.selectorText.startsWith('.') ? rule.selectorText.slice(1) : '';
					if (want.has(cls) && !out[cls]) {
						const s = rule.style;
						const wd = parseFloat(
							s.getPropertyValue('font-width') || s.getPropertyValue('font-stretch')
						);
						out[cls] = {
							size: parseFloat(s.getPropertyValue('font-size')),
							lh: parseFloat(s.getPropertyValue('line-height')),
							wt: parseInt(s.getPropertyValue('font-weight'), 10),
							wd: Number.isNaN(wd) ? 100 : wd
						};
					}
				} else if (rule instanceof CSSGroupingRule) {
					visit(rule.cssRules);
				}
			}
		};
		for (const sheet of Array.from(document.styleSheets)) {
			try {
				visit(sheet.cssRules);
			} catch {
				// Cross-origin stylesheet — not readable; skip.
			}
		}
		return out;
	}

	$effect(() => {
		if (typeof document === 'undefined') return;
		const html = document.documentElement;
		const prev = html.getAttribute('data-theme');

		const probe = document.createElement('div');
		probe.style.cssText = 'position:absolute;opacity:0;pointer-events:none';
		document.body.appendChild(probe);
		const canvas = document.createElement('canvas');
		canvas.width = canvas.height = 1;
		const ctx = canvas.getContext('2d', { willReadFrequently: true })!;

		// Returns per-hue contrast ratios; also captures concrete colors when asked.
		const measure = (capture?: Record<string, SurfaceColors>): Record<string, number> => {
			const out: Record<string, number> = {};
			for (const h of HUES) {
				const bg = resolve(probe, cssVar(tok(h, 'bg')));
				const fg = resolve(probe, cssVar(tok(h, 'fg')));
				if (capture) capture[h.name] = { bg, fg, border: resolve(probe, cssVar(tok(h, 'border'))) };
				out[h.name] = ratio(toRgb(ctx, bg), toRgb(ctx, fg));
			}
			return out;
		};

		const lc: Record<string, SurfaceColors> = {};
		html.setAttribute('data-theme', 'light');
		const light = measure(lc);
		html.setAttribute('data-theme', 'dark');
		const dark = measure();
		if (prev === null) html.removeAttribute('data-theme');
		else html.setAttribute('data-theme', prev);

		probe.remove();

		const merged: Record<string, Pair> = {};
		for (const h of HUES) merged[h.name] = { light: light[h.name], dark: dark[h.name] };
		contrasts = merged;
		lightColors = lc;
		typeMetrics = readUtilityMetrics();
	});

	const fmt = (n: number | undefined) => (n == null ? '—' : `${n.toFixed(2)}:1`);

	function onKey(e: KeyboardEvent, i: number) {
		if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
		e.preventDefault();
		const dir = e.key === 'ArrowRight' ? 1 : -1;
		const next = (i + dir + TABS.length) % TABS.length;
		active = TABS[next];
		document.getElementById(`tab-${TABS[next]}`)?.focus();
	}
</script>

<section class="tokens">
	<h1 class="title-md">Design Tokens</h1>

	<div class="tabs" role="tablist" aria-label="Design token groups">
		{#each TABS as name, i (name)}
			<button
				id={`tab-${name}`}
				class="tab"
				type="button"
				role="tab"
				aria-selected={active === name}
				aria-controls={`panel-${name}`}
				tabindex={active === name ? 0 : -1}
				onclick={() => (active = name)}
				onkeydown={(e) => onKey(e, i)}
			>
				{name}
			</button>
		{/each}
	</div>

	{#if activeHue}
		{@const h = activeHue}
		{@const c = contrasts[h.name]}
		<div id={`panel-${active}`} class="panel" role="tabpanel" aria-labelledby={`tab-${active}`}>
			<!-- Surface preview: the hue in context (bg + fg + border + shadow) -->
			<div
				class="preview"
				style="background:{cssVar(tok(h, 'bg'))};color:{cssVar(tok(h, 'fg'))};border-color:{cssVar(
					tok(h, 'border')
				)};box-shadow:{cssVar(tok(h, 'shadow'))}"
			>
				<span class="label-lg">{h.name}</span>
				<p class="body-md">The quick brown fox jumps over the lazy dog.</p>
			</div>

			<!-- bg/fg AAA contrast check -->
			<div class="contrast">
				<span class="label-md">bg / fg contrast (AAA ≥ {AAA_NORMAL}:1)</span>
				<span class="badge" class:fail={c && c.light < AAA_NORMAL}>light {fmt(c?.light)}</span>
				<span class="badge" class:fail={c && c.dark < AAA_NORMAL}>dark {fmt(c?.dark)}</span>
				{#if c && (c.light < AAA_NORMAL || c.dark < AAA_NORMAL)}
					<span class="error-text label-md">⚠ below AAA</span>
				{/if}
			</div>

			<!-- Individual token swatches -->
			<ul class="swatches">
				{#each h.parts as part (part)}
					{@const name = tok(h, part)}
					<li class="swatch">
						<span class="chip" style="background:{cssVar(name)}"></span>
						<code class="name">{name}</code>
					</li>
				{/each}
			</ul>
		</div>
	{:else if active === 'typography'}
		<!-- ── Typography ─────────────────────────────────────────────────────── -->
		{#snippet typeSample(t: Type)}
			{#if isDisplay(t)}
				<span class={t.cls}>{DISPLAY}</span>
			{:else if oneLine(t)}
				<span class={t.cls}>{LINE}</span>
			{:else if isCode(t)}
				<pre class={t.cls}>{CODE}</pre>
			{:else}
				<p class={t.cls}>{PARA1}</p>
				<p class={t.cls}>{PARA2}</p>
			{/if}
		{/snippet}
		{@const surf = typeSurface}
		{@const n = contrasts[surf.name]}
		{@const lc = lightColors[surf.name]}
		<div id="panel-typography" class="panel" role="tabpanel" aria-labelledby="tab-typography">
			<!-- Sub-tabs: render the samples on a chosen surface register -->
			<div class="subtabs" role="tablist" aria-label="Typography surface">
				{#each TYPE_SURFACES as name (name)}
					<button
						class="subtab"
						type="button"
						role="tab"
						aria-selected={typeSurfaceName === name}
						onclick={() => (typeSurfaceName = name)}
					>
						{name}
					</button>
				{/each}
			</div>

			<div class="type-head">
				<span class="col-role">token</span>
				<span class="col-meta">size / line · wt · wd</span>
				<span class="col-sample">light · fg on bg ({tok(surf, 'fg')} / {tok(surf, 'bg')})</span>
				<span class="col-sample">dark</span>
				<span class="col-aaa">AAA</span>
			</div>

			{#each TYPE as t (t.cls)}
				{@const m = typeMetrics[t.cls]}
				{@const thr = aaaThreshold(m)}
				{@const okL = n ? n.light >= thr : true}
				{@const okD = n ? n.dark >= thr : true}
				<div class="type-row">
					<code class="col-role name">{t.cls}</code>
					<span class="col-meta name"
						>{m ? `${m.size}/${m.lh} · ${m.wt} · ${m.wd}%` : '…'}</span
					>

					<div
						class="col-sample sample"
						style="background:{lc?.bg ?? cssVar(tok(surf, 'bg'))};color:{lc?.fg ??
							cssVar(tok(surf, 'fg'))};border-color:{lc?.border ?? cssVar(tok(surf, 'border'))}"
					>
						{@render typeSample(t)}
					</div>
					<div
						class="col-sample sample"
						data-theme="dark"
						style="background:{cssVar(tok(surf, 'bg'))};color:{cssVar(
							tok(surf, 'fg')
						)};border-color:{cssVar(tok(surf, 'border'))}"
					>
						{@render typeSample(t)}
					</div>

					<div class="col-aaa">
						<span class="badge" class:fail={!okL}>L {fmt(n?.light)}</span>
						<span class="badge" class:fail={!okD}>D {fmt(n?.dark)}</span>
						{#if !okL || !okD}
							<span class="error-text label-sm">⚠ &lt; {thr}:1</span>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{:else if active === 'elevation'}
		<!-- ── Elevation ──────────────────────────────────────────────────────── -->
		<div id="panel-elevation" class="panel" role="tabpanel" aria-labelledby="tab-elevation">
			<div class="elevations">
				{#each ELEVATIONS as level (level)}
					{@const none = level === 'none'}
					<div class="elevation-card" style="box-shadow:{none ? 'none' : `var(--elevation-${level})`}">
						<code class="name">{none ? 'box-shadow: none' : `--elevation-${level}`}</code>
					</div>
				{/each}
			</div>
		</div>
	{:else}
		<!-- ── Login card (each hue, light + dark) ───────────────────────────── -->
		{#snippet loginCard()}
			<form class="login-card" onsubmit={(e) => e.preventDefault()}>
				<h3 class="login-title heading-sm">Sign in</h3>
				<label class="login-field">
					<span class="label-md">Email</span>
					<input
						class="login-input body-sm"
						type="email"
						placeholder="you@example.com"
						autocomplete="off"
					/>
				</label>
				<label class="login-field">
					<span class="label-md">Password</span>
					<input
						class="login-input body-sm"
						type="password"
						placeholder="••••••••"
						autocomplete="off"
					/>
				</label>
				<button class="login-btn body-sm" type="submit">Log in</button>
			</form>
		{/snippet}

		{@const nLight = lightColors['neutral']}
		<div id="panel-login" class="panel" role="tabpanel" aria-labelledby="tab-login">
			{#each HUES as h (h.name)}
				{@const lc = lightColors[h.name]}
				<section class="login-hue">
					<h3 class="login-hue-name heading-sm">{h.name}</h3>
					<div class="login-cards">
						<div
							class="login-frame"
							style="background:{nLight?.bg ?? cssVar('--surface-bg')};color:{nLight?.fg ??
								cssVar('--surface-fg')};--lc-bg:{lc?.bg ?? cssVar(tok(h, 'bg'))};--lc-fg:{lc?.fg ??
								cssVar(tok(h, 'fg'))};--lc-border:{lc?.border ?? cssVar(tok(h, 'border'))}"
						>
							<span class="login-cap label-sm">light</span>
							{@render loginCard()}
						</div>
						<div
							class="login-frame"
							data-theme="dark"
							style="background:{cssVar('--surface-bg')};--lc-bg:{cssVar(tok(h, 'bg'))};--lc-fg:{cssVar(
								tok(h, 'fg')
							)};--lc-border:{cssVar(tok(h, 'border'))}"
						>
							<span class="login-cap label-sm">dark</span>
							{@render loginCard()}
						</div>
					</div>
				</section>
			{/each}
		</div>
	{/if}
</section>

<style>
	.tokens {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
		padding: 1.5rem;
		width: 90%;
		margin-inline: auto;
	}

	.tabs {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
		border-bottom: 1px solid var(--surface-border);
	}

	.tab {
		appearance: none;
		border: 1px solid transparent;
		border-bottom: none;
		border-radius: 0.5rem 0.5rem 0 0;
		padding: 0.5rem 0.9rem;
		background: transparent;
		color: var(--surface-fg);
		font-weight: 500;
		text-transform: capitalize;
		cursor: pointer;
		transition:
			background-color 120ms ease,
			box-shadow 120ms ease,
			color 120ms ease;
	}
	.tab:hover {
		background: var(--surface-bg-hover);
		color: var(--surface-border-bold);
		/* underline accent so the hover target reads as interactive */
		box-shadow: inset 0 -2px 0 var(--surface-border);
	}
	.tab[aria-selected='true'] {
		background: var(--surface-bg);
		border-color: var(--surface-border);
		margin-bottom: -1px;
	}
	.tab[aria-selected='true']:hover {
		box-shadow: none;
	}
	.tab:focus-visible {
		outline: 2px solid var(--surface-border-bold);
		outline-offset: 2px;
		border-radius: 0.5rem;
	}

	.panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.subtabs {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
		padding: 0.25rem;
		border-radius: 0.6rem;
		background: var(--surface-bg);
		border: 1px solid var(--surface-border);
		align-self: flex-start;
	}
	.subtab {
		appearance: none;
		border: 0;
		border-radius: 0.45rem;
		padding: 0.35rem 0.8rem;
		background: transparent;
		color: var(--surface-fg);
		font-weight: 500;
		text-transform: capitalize;
		cursor: pointer;
	}
	.subtab[aria-selected='true'] {
		background: var(--surface-bg-focus);
		box-shadow: var(--elevation-2xs);
	}
	.subtab:focus-visible {
		outline: 2px solid var(--surface-border-bold);
		outline-offset: 1px;
	}

	.preview {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 1.25rem;
		border: 1px solid;
		border-radius: 0.75rem;
	}

	.contrast {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.swatches {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 0.6rem;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.swatch {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 0.5rem;
		border: 1px solid var(--surface-border);
		border-radius: 0.6rem;
		background: transparent;
		color: var(--surface-fg);
	}
	.chip {
		flex: none;
		width: 2.5rem;
		height: 2.5rem;
		border-radius: 0.4rem;
		border: 1px solid var(--surface-border);
		box-shadow: var(--elevation-sm);
	}
	.name {
		font-family: var(--font-mono, ui-monospace, monospace);
		font-size: 0.78rem;
	}

	.badge {
		padding: 0.15rem 0.5rem;
		border-radius: 999px;
		border: 1px solid var(--surface-success-border, var(--surface-border));
		background: var(--surface-success-bg, var(--surface-bg));
		color: var(--surface-success-fg, var(--surface-fg));
		font-size: 0.72rem;
		font-family: var(--font-mono, ui-monospace, monospace);
		white-space: nowrap;
	}
	.badge.fail {
		border-color: var(--surface-error-border);
		background: var(--surface-error-bg);
		color: var(--surface-error-fg);
	}
	.error-text {
		color: var(--surface-error-fg);
	}

	/* Typography table */
	.type-head,
	.type-row {
		display: grid;
		grid-template-columns: 7rem 11rem minmax(25%, 1fr) minmax(25%, 1fr) 9rem;
		align-items: center;
		gap: 0.75rem;
	}
	.type-head {
		padding: 0 0.5rem 0.5rem;
		border-bottom: 1px solid var(--surface-border);
		font-size: 0.72rem;
		color: var(--surface-fg);
		opacity: 0.7;
	}
	.type-row {
		padding: 0.5rem;
		border-bottom: 1px solid var(--surface-border);
	}
	.col-meta {
		opacity: 0.8;
	}
	.sample {
		padding: 0.75rem;
		border-radius: 0.5rem;
		border: 1px solid var(--surface-border);
		background: var(--surface-bg);
		color: var(--surface-fg);
		box-shadow: var(--elevation-sm);
		overflow: hidden;
	}
	.sample p {
		margin: 0 0 0.6em;
	}
	.sample p:last-child {
		margin-bottom: 0;
	}
	.sample pre {
		margin: 0;
		font-family: var(--font-mono, ui-monospace, monospace);
		white-space: pre-wrap;
	}
	.col-aaa {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		align-items: flex-start;
	}

	/* Elevation */
	.elevations {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: 2.5rem;
		padding: 1.5rem 0.5rem 2.5rem;
	}
	.elevation-card {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 7rem;
		border-radius: 0.75rem;
		background: var(--surface-bg);
		color: var(--surface-fg);
		border: 1px solid var(--surface-border);
		box-shadow: var(--elevation-md);
	}

	/* Login showcase: per hue, light + dark each 40vw with a 10vw centre gap. */
	.login-hue {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.login-hue-name {
		margin: 0;
		text-transform: capitalize;
	}
	.login-cards {
		display: flex;
		justify-content: center;
		gap: 10vw;
		margin-inline: -1.5rem; /* cancel .tokens padding so 40+10+40 = 90vw fits */
	}
	.login-frame {
		flex: 0 0 40vw;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.6rem;
		padding: 1.75rem 1.25rem;
		border-radius: 0.9rem;
		border: 1px solid var(--surface-border);
		color: var(--surface-fg);
	}
	.login-cap {
		opacity: 0.7;
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}
	.login-card {
		display: flex;
		flex-direction: column;
		gap: 0.85rem;
		width: 100%;
		max-width: 300px;
		padding: 1.25rem;
		border-radius: 0.75rem;
		background: var(--lc-bg);
		color: var(--lc-fg);
		border: 1px solid var(--lc-border);
		box-shadow: var(--elevation-md);
	}
	.login-title {
		margin: 0;
	}
	.login-field {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	.login-input {
		padding: 0.5rem 0.65rem;
		border-radius: 0.5rem;
		border: 1px solid var(--lc-border);
		background: transparent;
		color: inherit;
		font: inherit;
		box-shadow: var(--elevation-sm);
		transition:
			background-color 120ms ease,
			border-color 120ms ease;
	}
	.login-input::placeholder {
		color: var(--lc-fg);
		opacity: 0.5;
	}
	.login-input:hover {
		background: color-mix(in oklab, var(--lc-fg) 6%, var(--lc-bg));
	}
	.login-input:focus {
		background: color-mix(in oklab, var(--lc-fg) 12%, var(--lc-bg));
		border-color: var(--lc-fg);
	}
	.login-input:focus-visible {
		outline: 2px solid var(--lc-fg);
		outline-offset: 1px;
	}
	.login-btn {
		margin-top: 0.3rem;
		padding: 0.55rem;
		border: 0;
		border-radius: 0.5rem;
		background: var(--lc-fg);
		color: var(--lc-bg);
		font-weight: 600;
		cursor: pointer;
		box-shadow: var(--elevation-sm);
	}
</style>
