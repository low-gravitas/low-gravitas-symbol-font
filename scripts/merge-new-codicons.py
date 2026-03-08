#!/usr/bin/env fontforge -script
"""Merge newer Codicons glyphs (U+EC1F-EC84) not present in the Nerd Fonts build."""

import os
import sys
import fontforge
import psMat

sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
from fontmetrics import lock_metrics

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

# Codicons in Nerd Fonts use native codepoints (U+EA60+)
# We want to copy glyphs in U+EC1F-EC84 that are in upstream but not in patched
count = 0
for codepoint in range(0xEC1F, 0xEC85):
    # Check if glyph exists in upstream
    source.selection.select(codepoint)
    source_glyphs = list(source.selection.byGlyphs)
    if not source_glyphs:
        continue

    # Check if glyph already exists in target
    try:
        existing = target[codepoint]
        if existing.isWorthOutputting():
            continue
    except TypeError:
        pass

    # Copy glyph from source to target
    source.selection.select(codepoint)
    source.copy()
    target.selection.select(codepoint)
    target.paste()

    g = target[codepoint]

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
    count += 1

print(f"Merged {count} new Codicon glyphs")

# Update font metadata
target.fontname = "LowGravitasSymbols"
target.familyname = "Low Gravitas Symbols"
target.fullname = "Low Gravitas Symbols"

lock_metrics(target)
target.generate(output_path)
print(f"Saved to {output_path}")
