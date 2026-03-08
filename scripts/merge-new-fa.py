#!/usr/bin/env fontforge -script
"""Merge newer Font Awesome glyphs not present in the Nerd Fonts build.

Font Awesome uses native PUA codepoints (U+E000-F8FF range), but Nerd Fonts
remaps them to U+ED00+. This script:
1. Builds a mapping of glyph names in the NF-bundled FA source
2. Finds glyphs in upstream FA that don't exist in the NF source
3. Assigns sequential codepoints starting after the last used NF FA codepoint
4. Copies and scales those glyphs into the patched font
"""

import os
import sys
import glob
import fontforge
import psMat

sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
from fontmetrics import lock_metrics

if len(sys.argv) < 4:
    print("Usage: fontforge -script merge-new-fa.py <patched.ttf> <upstream-fa-dir/> <output.ttf>")
    sys.exit(1)

patched_path = sys.argv[1]
upstream_dir = sys.argv[2]
output_path = sys.argv[3]

target = fontforge.open(patched_path)

# Determine cell width from existing glyphs
cell_width = None
for glyph in target.glyphs():
    if glyph.width > 0:
        cell_width = glyph.width
        break
if cell_width is None:
    cell_width = target.em

# Find the NF-bundled Font Awesome source to build the existing glyph name set
nf_fa_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))),
                           "vendor", "src", "glyphs", "font-awesome", "FontAwesome.otf")
if not os.path.exists(nf_fa_path):
    # Try relative to cwd
    nf_fa_path = "vendor/src/glyphs/font-awesome/FontAwesome.otf"

print(f"Loading NF-bundled FA from: {nf_fa_path}")
nf_fa = fontforge.open(nf_fa_path)

# Build set of glyph names in the NF-bundled FA
nf_glyph_names = set()
for glyph in nf_fa.glyphs():
    if glyph.isWorthOutputting():
        nf_glyph_names.add(glyph.glyphname)

print(f"NF-bundled FA has {len(nf_glyph_names)} glyphs")
nf_fa.close()

# Find the last used codepoint in the NF FA range (ED00+) in the target
last_nf_fa_cp = 0xED00
for codepoint in range(0xED00, 0xF300):
    try:
        g = target[codepoint]
        if g.isWorthOutputting():
            last_nf_fa_cp = codepoint
    except TypeError:
        pass

next_cp = last_nf_fa_cp + 1
print(f"Last NF FA codepoint in target: U+{last_nf_fa_cp:04X}, will assign new glyphs from U+{next_cp:04X}")

# Find upstream FA OTF files
upstream_otfs = glob.glob(os.path.join(upstream_dir, "**", "*.otf"), recursive=True)
if not upstream_otfs:
    print("No upstream FA OTF files found, skipping FA merge")
    lock_metrics(target)
    target.generate(output_path)
    sys.exit(0)

print(f"Found upstream FA fonts: {upstream_otfs}")

count = 0
for otf_path in upstream_otfs:
    print(f"Processing {otf_path}...")
    source = fontforge.open(otf_path)
    scale_factor = target.em / source.em if target.em != source.em else 1.0

    for glyph in source.glyphs():
        if not glyph.isWorthOutputting():
            continue
        if glyph.glyphname in nf_glyph_names:
            continue
        if glyph.glyphname.startswith("."):
            continue

        # Skip to next free codepoint (avoid collisions with Font Logos, Octicons, Material Design, etc.)
        while True:
            try:
                existing = target[next_cp]
                if existing.isWorthOutputting():
                    next_cp += 1
                    continue
            except TypeError:
                pass
            break

        # This is a new glyph — assign it the next available codepoint
        source.selection.select(glyph.glyphname)
        source.copy()
        target.createChar(next_cp, glyph.glyphname)
        target.selection.select(next_cp)
        target.paste()

        g = target[next_cp]

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
        nf_glyph_names.add(glyph.glyphname)  # avoid duplicates across FA variants
        next_cp += 1
        count += 1

    source.close()

print(f"Merged {count} new Font Awesome glyphs (U+{last_nf_fa_cp + 1:04X}–U+{next_cp - 1:04X})")

target.fontname = "LowGravitasSymbols"
target.familyname = "Low Gravitas Symbols"
target.fullname = "Low Gravitas Symbols"

lock_metrics(target)
target.generate(output_path)
print(f"Saved to {output_path}")
