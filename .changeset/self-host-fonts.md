---
'@wimwian/smuit-theme': minor
---

Self-host the theme's Google Fonts. `scripts/fetch-fonts.mjs` downloads Noto Sans Display, Noto Sans Mono, and Google Sans Code (latin + latin-ext woff2 subsets) into `src/assets/fonts/` and emits a `fonts.css` with `@font-face` rules pointing at the local files. The fonts ship in the published package and are exposed via the new `@wimwian/smuit-theme/fonts.css` entry point, so consumers can use the fonts without a Google Fonts `<link>`.
