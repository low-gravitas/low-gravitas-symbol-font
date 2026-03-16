#!/usr/bin/env fontforge -script
"""Merge custom Low Gravitas glyphs from SVGs in the glyphs/ directory.

Custom glyphs are assigned codepoints starting at U+E900 (between Devicons and Codicons).
Each SVG filename (minus extension) becomes the glyph name.
"""

import os
import sys
import glob
import fontforge
import psMat

sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
from fontmetrics import lock_metrics
from ranges import NF_RANGES, OVERFLOW_RANGES

if len(sys.argv) < 3:
    print("Usage: fontforge -script merge-custom-glyphs.py <input.ttf> <output.ttf>")
    sys.exit(1)

input_path = sys.argv[1]
output_path = sys.argv[2]

target = fontforge.open(input_path)

# Determine cell width from existing glyphs
cell_width = None
for glyph in target.glyphs():
    if glyph.width > 0:
        cell_width = glyph.width
        break
if cell_width is None:
    cell_width = target.em

# Find custom SVGs
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
glyphs_dir = os.path.join(script_dir, "glyphs")
if not os.path.isdir(glyphs_dir):
    glyphs_dir = "glyphs"

svgs = sorted(glob.glob(os.path.join(glyphs_dir, "*.svg")))
if not svgs:
    print("No custom SVGs found in glyphs/, skipping")
    lock_metrics(target)
    target.generate(output_path)
    sys.exit(0)

print(f"Found {len(svgs)} custom glyph(s) in {glyphs_dir}")

# Pinned codepoints: glyphs listed here always get their assigned codepoint,
# regardless of filename sort order. This prevents existing codepoints from
# shifting when new glyphs are added.
PINNED_CODEPOINTS = {
    "low-gravitas": 0xE900,
    "kajabi":       0xE901,
}

# Process pinned glyphs first (in codepoint order), then unpinned (alphabetical)
pinned_svgs = []
unpinned_svgs = []
for svg_path in svgs:
    name = os.path.splitext(os.path.basename(svg_path))[0]
    if name in PINNED_CODEPOINTS:
        pinned_svgs.append(svg_path)
    else:
        unpinned_svgs.append(svg_path)
pinned_svgs.sort(key=lambda p: PINNED_CODEPOINTS[os.path.splitext(os.path.basename(p))[0]])
ordered_svgs = pinned_svgs + unpinned_svgs

custom_primary_end = NF_RANGES["Custom (Low Gravitas)"][1]
custom_overflow_start, custom_overflow_end = OVERFLOW_RANGES["Custom (Low Gravitas)"]
used_cps = set(PINNED_CODEPOINTS.values())
next_cp = 0xE900
count = 0

for svg_path in ordered_svgs:
    name = os.path.splitext(os.path.basename(svg_path))[0]

    if name in PINNED_CODEPOINTS:
        cp = PINNED_CODEPOINTS[name]
    else:
        # Find next free codepoint, skipping pinned ones
        while next_cp in used_cps:
            next_cp += 1
        if next_cp > custom_primary_end and next_cp < custom_overflow_start:
            print(f"Primary custom range full at U+{custom_primary_end:04X}, continuing in overflow range U+{custom_overflow_start:05X}+")
            next_cp = custom_overflow_start
        if next_cp > custom_overflow_end:
            print(f"ERROR: Custom glyph overflow range exhausted at U+{custom_overflow_end:05X}")
            sys.exit(1)
        cp = next_cp
        next_cp += 1

    glyph = target.createChar(cp, name)
    glyph.importOutlines(svg_path)

    # Scale to fit within the em square
    bbox = glyph.boundingBox()
    if bbox[2] - bbox[0] > 0 and bbox[3] - bbox[1] > 0:
        svg_width = bbox[2] - bbox[0]
        svg_height = bbox[3] - bbox[1]
        target_size = target.em * 0.9
        scale = min(target_size / svg_width, target_size / svg_height)
        glyph.transform(psMat.scale(scale))

        # Center within cell
        bbox = glyph.boundingBox()
        x_offset = (cell_width - (bbox[2] - bbox[0])) / 2 - bbox[0]
        target_mid = (target.ascent - target.descent) / 2.0
        glyph_mid = (bbox[1] + bbox[3]) / 2.0
        y_offset = target_mid - glyph_mid
        glyph.transform(psMat.translate(x_offset, y_offset))

    glyph.width = cell_width
    print(f"  U+{cp:04X} {name} <- {os.path.basename(svg_path)}")
    count += 1

print(f"Merged {count} custom glyph(s)")

target.fontname = "LowGravitasSymbols"
target.familyname = "Low Gravitas Symbols"
target.fullname = "Low Gravitas Symbols"

lock_metrics(target)
target.generate(output_path)
print(f"Saved to {output_path}")
