// Copyright (c) 2026 @wimwian
// SPDX-License-Identifier: MIT

import { afterEach, expect, test } from 'vitest';
import { page } from 'vitest/browser';
import { render } from 'vitest-browser-svelte';
import ThemeToggle from './ThemeToggle.svelte';

afterEach(() => {
	document.documentElement.removeAttribute('data-theme');
	localStorage.clear();
});

test('renders a labelled toggle button', async () => {
	render(ThemeToggle);
	await expect.element(page.getByRole('button', { name: /toggle color theme/i })).toBeInTheDocument();
});

test('shows the sun in light mode and flips to the moon on click', async () => {
	document.documentElement.dataset.theme = 'light';
	render(ThemeToggle);

	const btn = page.getByRole('button', { name: /toggle color theme/i });
	// Light → sun icon, not pressed.
	await expect.element(btn).toHaveAttribute('aria-pressed', 'false');
	await expect.element(btn).toHaveAttribute('title', 'Switch to dark theme');

	await btn.click();

	// Dark → moon icon, pressed, and the document register flipped.
	await expect.element(btn).toHaveAttribute('aria-pressed', 'true');
	expect(document.documentElement.dataset.theme).toBe('dark');
});

test('merges a consumer-supplied class', async () => {
	render(ThemeToggle, { class: 'my-toggle' });
	const btn = page.getByRole('button');
	await expect.element(btn).toHaveClass(/theme-toggle/);
	await expect.element(btn).toHaveClass(/my-toggle/);
});
