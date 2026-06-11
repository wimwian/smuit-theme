// Copyright (c) 2026 @wimwian
// SPDX-License-Identifier: MIT

// Runs in the browser project (needs a real `document` + `localStorage`).

import { afterEach, expect, test } from 'vitest';
import { getTheme, setTheme, toggleTheme, initTheme } from './theme.js';

afterEach(() => {
	document.documentElement.removeAttribute('data-theme');
	localStorage.clear();
});

test('setTheme writes the attribute and persists it', () => {
	setTheme('dark');
	expect(document.documentElement.dataset.theme).toBe('dark');
	expect(localStorage.getItem('theme')).toBe('dark');
});

test('getTheme reflects an explicit data-theme', () => {
	document.documentElement.dataset.theme = 'dark';
	expect(getTheme()).toBe('dark');
});

test('toggleTheme flips and returns the new value', () => {
	setTheme('light');
	expect(toggleTheme()).toBe('dark');
	expect(getTheme()).toBe('dark');
	expect(toggleTheme()).toBe('light');
});

test('initTheme restores a persisted preference', () => {
	localStorage.setItem('theme', 'dark');
	expect(initTheme()).toBe('dark');
	expect(document.documentElement.dataset.theme).toBe('dark');
});
