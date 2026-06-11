# @wimwian/smuit-theme

## 0.2.0

### Minor Changes

- 7cf5939: Self-host the theme's Google Fonts. `scripts/fetch-fonts.mjs` downloads Noto Sans Display, Noto Sans Mono, and Google Sans Code (latin + latin-ext woff2 subsets) into `src/assets/fonts/` and emits a `fonts.css` with `@font-face` rules pointing at the local files. The fonts ship in the published package and are exposed via the new `@wimwian/smuit-theme/fonts.css` entry point, so consumers can use the fonts without a Google Fonts `<link>`.

## 0.1.0

### Minor Changes

- First minor release. SvelteKit theme package with oklch design tokens, a Tailwind v4 theme, and the `ThemeToggle` component, alongside the Python theme generator (`theme-input.toml` → `output.css`) and the full commit/release toolchain (commitlint, lefthook, changesets).
