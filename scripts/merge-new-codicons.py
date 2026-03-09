#!/usr/bin/env fontforge -script
"""Merge newer Codicons glyphs not present in the Nerd Fonts build.

Codicons use native codepoints (U+EA60+). This script:
1. Builds a set of glyph names from the NF-bundled Codicons source
2. Finds glyphs in upstream Codicons not in the NF set
3. For glyphs whose native codepoint is free in the target, places them there
4. Otherwise assigns sequential codepoints after the last used Codicons codepoint
5. Overflows to Supplementary PUA-A if the primary range fills up
"""

import os
import sys
import fontforge
import psMat

sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
from fontmetrics import lock_metrics
from ranges import NF_RANGES, OVERFLOW_RANGES

if len(sys.argv) < 4:
    print("Usage: fontforge -script merge-new-codicons.py <patched.ttf> <upstream-codicon.ttf> <output.ttf>")
    sys.exit(1)

patched_path = sys.argv[1]
upstream_path = sys.argv[2]
output_path = sys.argv[3]

target = fontforge.open(patched_path)
source = fontforge.open(upstream_path)

# Determine scaling factor if em sizes differ
scale_factor = target.em / source.em if target.em != source.em else 1.0

# Determine the cell width from existing glyphs in the target
cell_width = None
for glyph in target.glyphs():
    if glyph.width > 0:
        cell_width = glyph.width
        break

if cell_width is None:
    cell_width = target.em  # fallback

print(f"Target em: {target.em}, Source em: {source.em}, Scale: {scale_factor}")
print(f"Cell width: {cell_width}")

# Find the NF-bundled Codicons source to build the existing glyph name set
nf_cod_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))),
                            "vendor", "src", "glyphs", "codicons", "codicon.ttf")
if not os.path.exists(nf_cod_path):
    nf_cod_path = "vendor/src/glyphs/codicons/codicon.ttf"

print(f"Loading NF-bundled Codicons from: {nf_cod_path}")
nf_cod = fontforge.open(nf_cod_path)

# Build set of glyph names in the NF-bundled Codicons
nf_glyph_names = set()
for glyph in nf_cod.glyphs():
    if glyph.isWorthOutputting():
        nf_glyph_names.add(glyph.glyphname)

print(f"NF-bundled Codicons has {len(nf_glyph_names)} glyphs")
nf_cod.close()

# Find the last used codepoint in the NF Codicons range in the target
cod_primary_start, cod_primary_end = NF_RANGES["Codicons"]
last_nf_cod_cp = cod_primary_start
for codepoint in range(cod_primary_start, cod_primary_end + 1):
    try:
        g = target[codepoint]
        if g.isWorthOutputting():
            last_nf_cod_cp = codepoint
    except TypeError:
        pass

next_cp = last_nf_cod_cp + 1
print(f"Last NF Codicons codepoint in target: U+{last_nf_cod_cp:04X}, will assign new glyphs from U+{next_cp:04X}")

# Collect new glyphs from upstream
new_glyphs = []
for glyph in source.glyphs():
    if not glyph.isWorthOutputting():
        continue
    if glyph.glyphname in nf_glyph_names:
        continue
    if glyph.glyphname.startswith("."):
        continue
    new_glyphs.append((glyph.unicode, glyph.glyphname))

print(f"Found {len(new_glyphs)} new Codicon glyphs to merge")

cod_overflow_start, cod_overflow_end = OVERFLOW_RANGES["Codicons"]
in_overflow = False

def find_next_free_cp():
    """Advance next_cp to the next free slot, respecting range boundaries."""
    global next_cp, in_overflow
    while True:
        if not in_overflow and next_cp > cod_primary_end:
            print(f"Primary Codicons range full at U+{cod_primary_end:04X}, continuing in overflow range U+{cod_overflow_start:05X}+")
            next_cp = cod_overflow_start
            in_overflow = True
        if in_overflow and next_cp > cod_overflow_end:
            print(f"ERROR: Codicons overflow range exhausted at U+{cod_overflow_end:05X}")
            sys.exit(1)
        try:
            existing = target[next_cp]
            if existing.isWorthOutputting():
                next_cp += 1
                continue
        except TypeError:
            pass
        break

count = 0
for src_cp, glyphname in sorted(new_glyphs):
    # Try to place at the native codepoint if it's within the Codicons range and free
    placed_cp = None
    if cod_primary_start <= src_cp <= cod_primary_end:
        try:
            existing = target[src_cp]
            if not existing.isWorthOutputting():
                placed_cp = src_cp
        except TypeError:
            placed_cp = src_cp

    if placed_cp is None:
        find_next_free_cp()
        placed_cp = next_cp
        next_cp += 1

    # Copy glyph from source to target
    source.selection.select(glyphname)
    source.copy()
    target.createChar(placed_cp, glyphname)
    target.selection.select(placed_cp)
    target.paste()

    g = target[placed_cp]

    # Scale to target em
    if scale_factor != 1.0:
        g.transform(psMat.scale(scale_factor))

    # Scale glyph to fill 90% of em square
    bbox = g.boundingBox()
    gw = bbox[2] - bbox[0]
    gh = bbox[3] - bbox[1]
    if gw > 0 and gh > 0:
        target_size = target.em * 0.9
        fill_scale = target_size / max(gw, gh)
        g.transform(psMat.scale(fill_scale))

        # Center horizontally within cell, vertically within em
        bbox = g.boundingBox()
        x_off = (cell_width - (bbox[2] - bbox[0])) / 2.0 - bbox[0]
        target_mid = (target.ascent - target.descent) / 2.0
        glyph_mid = (bbox[1] + bbox[3]) / 2.0
        y_off = target_mid - glyph_mid
        g.transform(psMat.translate(x_off, y_off))

    g.width = cell_width
    nf_glyph_names.add(glyphname)  # avoid duplicates
    count += 1

if count > 0:
    print(f"Merged {count} new Codicon glyphs")
else:
    print("No new Codicon glyphs to merge")

source.close()

# Update font metadata
target.fontname = "LowGravitasSymbols"
target.familyname = "Low Gravitas Symbols"
target.fullname = "Low Gravitas Symbols"

lock_metrics(target)
target.generate(output_path)
print(f"Saved to {output_path}")
