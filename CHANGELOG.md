# @smuit/smuit-theme

## 0.3.0

### Minor Changes

- e500dff: Rename the package to `@smuit/smuit-theme` and move the repository to the `smuit` GitHub org. Consumers must update their imports from `@wimwian/smuit-theme` to `@smuit/smuit-theme` — including the subpath entry points `@smuit/smuit-theme/fonts.css`, `@smuit/smuit-theme/theme.minified.css`, and `@smuit/smuit-theme/ThemeToggle.svelte`. The package now publishes to the `smuit` org's GitHub Packages registry.
- e500dff: Typography updates: increase the `body` (xs–xl) and `label` (sm–lg) type-scale font sizes, and adjust the `display-md` line-height. The generated theme stylesheet now emits the standard `font-stretch` property in place of the previous non-standard `font-width`.

## 0.2.0

### Minor Changes

- 7cf5939: Self-host the theme's Google Fonts. `scripts/fetch-fonts.mjs` downloads Noto Sans Display, Noto Sans Mono, and Google Sans Code (latin + latin-ext woff2 subsets) into `src/assets/fonts/` and emits a `fonts.css` with `@font-face` rules pointing at the local files. The fonts ship in the published package and are exposed via the new `@wimwian/smuit-theme/fonts.css` entry point, so consumers can use the fonts without a Google Fonts `<link>`.

## 0.1.0

### Minor Changes

- First minor release. SvelteKit theme package with oklch design tokens, a Tailwind v4 theme, and the `ThemeToggle` component, alongside the Python theme generator (`theme-input.toml` → `output.css`) and the full commit/release toolchain (commitlint, lefthook, changesets).
