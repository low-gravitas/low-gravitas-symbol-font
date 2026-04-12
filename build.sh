#!/bin/bash
set -euo pipefail

if ! command -v fontforge &>/dev/null; then
  echo "ERROR: fontforge is not installed."
  echo "  brew install fontforge"
  exit 1
fi

if [ ! -d vendor/src/glyphs ]; then
  echo "ERROR: vendor/src/glyphs not found. Run 'make update' first."
  exit 1
fi

mkdir -p build/ dist/

echo "=== Step 1: Build base font from NF glyph sources ==="
fontforge -script scripts/build-font.py \
  vendor/src/glyphs build/base.ttf

echo "=== Step 2: Merge custom glyphs (U+E900+) ==="
fontforge -script scripts/merge-custom-glyphs.py \
  build/base.ttf build/step2.ttf

echo "=== Step 3: Merge newer Codicons (U+EC1F-EC84) ==="
fontforge -script scripts/merge-new-codicons.py \
  build/step2.ttf vendor/upstream-codicons/codicon.ttf build/step3.ttf

echo "=== Step 4: Merge newer Font Awesome glyphs ==="
fontforge -script scripts/merge-new-fa.py \
  build/step3.ttf vendor/upstream-fa/ build/step4.ttf

echo "=== Step 5: Merge newer Octicons from SVGs ==="
fontforge -script scripts/merge-new-octicons.py \
  build/step4.ttf vendor/upstream-octicons/ dist/LowGravitasSymbols.ttf

echo ""
echo "=== Step 6: Generate glyph manifest ==="
fontforge -script scripts/generate-manifest.py \
  dist/LowGravitasSymbols.ttf dist/glyphs.json

echo ""
echo "=== Build complete ==="
echo "Output: dist/LowGravitasSymbols.ttf"
echo "Manifest: dist/glyphs.json"
echo "CSS: dist/low-gravitas-symbols.css"
