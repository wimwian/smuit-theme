---
'@smuit/smuit-theme': minor
---

Rename the package to `@smuit/smuit-theme` and move the repository to the `smuit` GitHub org. Consumers must update their imports from `@wimwian/smuit-theme` to `@smuit/smuit-theme` — including the subpath entry points `@smuit/smuit-theme/fonts.css`, `@smuit/smuit-theme/theme.minified.css`, and `@smuit/smuit-theme/ThemeToggle.svelte`. The package now publishes to the `smuit` org's GitHub Packages registry.
