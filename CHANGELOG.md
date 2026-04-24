# Changelog

## [0.3.2] - 2026-04-24

### Added
- Codepoint pin registry (`scripts/pins.py`, `glyphs/codicons-pins.json`,
  `glyphs/fa-pins.json`, `glyphs/octicons-pins.json`) — each merge script
  records glyph name → codepoint assignments after each build and reuses
  them on subsequent builds, preventing codepoint churn across releases

### Fixed
- Overflow codepoint instability: adding a new upstream glyph that sorts
  before existing overflow glyphs no longer displaces their codepoints
- Non-deterministic builds: refreshing the NF-bundled Codicons source could
  shift which glyphs our merge scripts considered "new", causing different
  codepoints to be assigned on each CI run

### Removed
- `share-window` Codicons glyph — was an artifact of an unlocked upstream
  build prior to `sources.lock.json`; not present in pinned Codicons 0.0.46-5

## [0.3.1] - 2026-04-23

### Added
- WOFF2 build output (`dist/LowGravitasSymbols.woff2`) — 42% smaller than TTF,
  generated automatically from the TTF via `woff2_compress` as a new build step
- WOFF2 listed first in the generated `@font-face` src in `low-gravitas-symbols.css`,
  with TTF as fallback for environments that don't support WOFF2
- `woff2_compress` prerequisite check in `build.sh` (`brew install woff2`)

## [0.3.0] - 2026-03-15

### Fixed
- 18 Powerline Extra glyph names (E0C0–E0D7) corrected to match Nerd Fonts
  canonical names — e.g. "trapezoid-right-solid" → "pixelated-squares-small"

### Added
- Kajabi mark glyph at U+E901 using diagonal hatching for three-shade logo
- Pinned codepoint system for custom glyphs — prevents codepoint shifts when
  new glyphs are added
- Glyph detail modal with 72px specimen, copy actions (symbol, codepoint, UTF
  escape, CSS class, deep link), and prev/next navigation
- Finder-style keyboard interaction: roving tabindex grid navigation, Space to
  inspect, Enter to collect, Shift+Arrow/Shift+Click for range collection,
  Cmd/Ctrl+Click for single toggle, Cmd/Ctrl+A for batch collection
- Hex code search (e.g. "E0C4", "U+E0C4", "0xE0C4")
- Sort toggle (name or codepoint)
- WCAG 2.1 AA accessibility: focus trap, focus restoration, aria-labels,
  aria-live regions, sr-only labels, skip-to-content link,
  prefers-reduced-motion, keyboard-accessible cards and selection panel
- Low Gravitas Zen color theme with warm-toned dark/light modes
- Sticky footer on glyph browser page

### Changed
- CSS extracted into common.css, browser.css, and index.css (no more inline)
- Surface hierarchy: --surface-raised for chrome, --bg for content, --surface
  for mid-level elements
- Selection renamed to "collection" throughout for conceptual clarity
- GitHub org updated from mikeabney to low-gravitas
- Heading hierarchy fixed on index.html (h3 → h2)
- Brand glyph enlarged to 2em in nav header

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
