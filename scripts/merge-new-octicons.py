#!/usr/bin/env fontforge -script
"""Merge newer Octicons glyphs not present in the Nerd Fonts build.

Upstream Octicons are distributed as SVGs (no font file). This script:
1. Builds a set of glyph names from the NF-bundled Octicons source
2. Scans upstream SVGs for icons not in the NF set
3. Imports the SVGs into FontForge, scales them to match the target em/cell
4. Assigns sequential codepoints continuing the NF Octicons range

Prefers 16px variants over 24px for terminal single-cell rendering.
"""

import os
import sys
import glob
import fontforge
import psMat

sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
from fontmetrics import lock_metrics

if len(sys.argv) < 4:
    print("Usage: fontforge -script merge-new-octicons.py <patched.ttf> <upstream-octicons-dir/> <output.ttf>")
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

# Find the NF-bundled Octicons source
nf_oct_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))),
                            "vendor", "src", "glyphs", "octicons", "octicons.otf")
if not os.path.exists(nf_oct_path):
    nf_oct_path = "vendor/src/glyphs/octicons/octicons.otf"

print(f"Loading NF-bundled Octicons from: {nf_oct_path}")
nf_oct = fontforge.open(nf_oct_path)

# Build set of glyph names in the NF-bundled Octicons
nf_glyph_names = set()
for glyph in nf_oct.glyphs():
    if glyph.isWorthOutputting():
        nf_glyph_names.add(glyph.glyphname)

print(f"NF-bundled Octicons has {len(nf_glyph_names)} glyphs")
nf_oct.close()

# Find the last used codepoint in the NF Octicons range (F400+) in the target
last_nf_oct_cp = 0xF400
for codepoint in range(0xF400, 0xF500):
    try:
        g = target[codepoint]
        if g.isWorthOutputting():
            last_nf_oct_cp = codepoint
    except TypeError:
        pass

next_cp = last_nf_oct_cp + 1
print(f"Last NF Octicons codepoint in target: U+{last_nf_oct_cp:04X}, will assign new glyphs from U+{next_cp:04X}")

# Find upstream SVGs
svg_dir = None
for candidate in [
    os.path.join(upstream_dir, "package", "build", "svg"),
    os.path.join(upstream_dir, "build", "svg"),
    upstream_dir,
]:
    if os.path.isdir(candidate):
        svgs = glob.glob(os.path.join(candidate, "*.svg"))
        if svgs:
            svg_dir = candidate
            break

if not svg_dir:
    print("No upstream Octicons SVGs found, skipping Octicons merge")
    lock_metrics(target)
    target.generate(output_path)
    sys.exit(0)

all_svgs = sorted(glob.glob(os.path.join(svg_dir, "*.svg")))
print(f"Found {len(all_svgs)} SVGs in {svg_dir}")

# Group SVGs by icon name, preferring 16px variants
# Naming convention: icon-name-16.svg, icon-name-24.svg
icons = {}  # name -> svg_path
for svg_path in all_svgs:
    basename = os.path.splitext(os.path.basename(svg_path))[0]
    # Split off the size suffix
    parts = basename.rsplit("-", 1)
    if len(parts) == 2 and parts[1] in ("12", "16", "24", "48", "96"):
        name = parts[0]
        size = int(parts[1])
    else:
        name = basename
        size = 0

    if name not in icons:
        icons[name] = (size, svg_path)
    else:
        existing_size = icons[name][0]
        # Prefer 16px, then smallest available
        if size == 16 or (existing_size != 16 and size < existing_size):
            icons[name] = (size, svg_path)

print(f"Unique icon names: {len(icons)}")

# Import new icons
count = 0
for name in sorted(icons.keys()):
    if name in nf_glyph_names:
        continue

    _, svg_path = icons[name]

    # Skip to next free codepoint (avoid collisions with other glyph sets)
    while True:
        try:
            existing = target[next_cp]
            if existing.isWorthOutputting():
                next_cp += 1
                continue
        except TypeError:
            pass
        break

    # Create glyph and import SVG
    glyph = target.createChar(next_cp, name)
    glyph.importOutlines(svg_path)

    # Scale the imported outline to fill 90% of em square
    bbox = glyph.boundingBox()  # (xmin, ymin, xmax, ymax)
    if bbox[2] - bbox[0] > 0 and bbox[3] - bbox[1] > 0:
        svg_width = bbox[2] - bbox[0]
        svg_height = bbox[3] - bbox[1]
        target_size = target.em * 0.9
        scale = target_size / max(svg_width, svg_height)
        glyph.transform(psMat.scale(scale))

        # Center horizontally within cell, vertically within em
        bbox = glyph.boundingBox()
        x_offset = (cell_width - (bbox[2] - bbox[0])) / 2.0 - bbox[0]
        target_mid = (target.ascent - target.descent) / 2.0
        glyph_mid = (bbox[1] + bbox[3]) / 2.0
        y_offset = target_mid - glyph_mid
        glyph.transform(psMat.translate(x_offset, y_offset))

    glyph.width = cell_width
    next_cp += 1
    count += 1

if count > 0:
    print(f"Merged {count} new Octicons glyphs (U+{last_nf_oct_cp + 1:04X}--U+{next_cp - 1:04X})")
else:
    print("No new Octicons glyphs to merge")

target.fontname = "LowGravitasSymbols"
target.familyname = "Low Gravitas Symbols"
target.fullname = "Low Gravitas Symbols"

lock_metrics(target)
target.generate(output_path)
print(f"Saved to {output_path}")
