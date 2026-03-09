# Changelog

## [0.2.0] - 2026-03-09

### Fixed
- Font Awesome glyphs no longer overflow into Font Logos (U+F300–F381) and
  Octicons (U+F400–FA10) codepoint ranges — 1,307 glyphs that previously
  collided are now placed in a dedicated overflow range (U+F1B00+)
- Glyph browser site now shows correct set labels for all glyphs (e.g. the
  `claude` glyph correctly shows "Font Awesome" instead of "Octicons")
- Octicons scan range in `merge-new-octicons.py` extended from U+F500 to
  U+FA11 to cover the full NF Octicons range
- Codicons merge script rewritten to use name-based matching (like FA/Octicons)
  instead of a hardcoded codepoint range

### Added
- `scripts/ranges.py` — shared module defining all NF codepoint ranges and
  overflow ranges as a single source of truth
- Overflow protection in all merge scripts: when a primary NF range fills up,
  new glyphs are redirected to designated overflow ranges in Supplementary
  PUA-A (U+F1B00+) instead of silently colliding with other glyph sets
- Overflow ranges for Font Awesome, Octicons, Custom, and Codicons
- 104 new Codicons glyphs including `claude`, `openai`, `ask`, `copilot-*`,
  and more

### Changed
- `generate-manifest.py` imports range definitions from the shared module
  instead of maintaining a separate hardcoded list
- Codicons source switched from npm `@vscode/codicons` (stale stable release)
  to the GitHub Pages build, which tracks the main branch and includes the
  latest glyphs (536 vs 525 previously)
- `merge-new-codicons.py` now discovers new glyphs by name comparison against
  the NF-bundled source, placing them at native codepoints when possible

## [0.1.1] - 2025-12-15

### Added
- GitHub Actions release workflow
- VERSION tracking file

## [0.1.0] - 2025-12-15

### Added
- Initial release of Low Gravitas Symbols font
- Merges all Nerd Fonts glyph sets into a single symbol-only font
- Custom glyph support (SVGs in `glyphs/` directory)
- Upstream Font Awesome, Codicons, and Octicons merging
- GitHub Pages glyph browser site
