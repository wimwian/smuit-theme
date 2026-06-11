// Copyright (c) 2026 @wimwian
// SPDX-License-Identifier: MIT

// Theme register management — writes the `data-theme` attribute the design
// tokens key off, and persists the choice. SSR-safe: every DOM access guards
// on `typeof document`.

export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'theme';

/** Current theme: explicit `data-theme` wins, else OS preference, else light. */
export function getTheme(): Theme {
	if (typeof document === 'undefined') return 'light';
	const attr = document.documentElement.dataset.theme;
	if (attr === 'light' || attr === 'dark') return attr;
	return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/** Apply a theme to the document and persist it. */
export function setTheme(theme: Theme): void {
	if (typeof document === 'undefined') return;
	document.documentElement.dataset.theme = theme;
	try {
		localStorage.setItem(STORAGE_KEY, theme);
	} catch {
		// Storage may be unavailable (private mode, blocked cookies) — non-fatal.
	}
}

/** Flip between light and dark; returns the new theme. */
export function toggleTheme(): Theme {
	const next: Theme = getTheme() === 'dark' ? 'light' : 'dark';
	setTheme(next);
	return next;
}

/** Restore a persisted preference on load. Call once in the root layout. */
export function initTheme(): Theme {
	if (typeof document === 'undefined') return 'light';
	let stored: Theme | null = null;
	try {
		const v = localStorage.getItem(STORAGE_KEY);
		if (v === 'light' || v === 'dark') stored = v;
	} catch {
		// Ignore storage read failures.
	}
	const theme = stored ?? getTheme();
	setTheme(theme);
	return theme;
}
