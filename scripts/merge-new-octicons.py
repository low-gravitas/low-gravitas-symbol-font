#!/usr/bin/env fontforge -script
"""Merge newer Octicons glyphs not present in the Nerd Fonts build.

Codepoint assignment strategy:
- Glyphs previously assigned a codepoint are recorded in glyphs/octicons-pins.json.
  On each build those glyphs are placed at their pinned codepoints (pass 1), so
  upstream renames or reorderings never shift existing assignments.
- Truly new glyph names are placed sequentially in pass 2, continuing the NF
  Octicons range (U+F400–U+FA10) or into overflow (U+F3000+).
  All placements are added to the pins file for future stability.

Prefers 16px SVG variants over 24px for terminal single-cell rendering.
"""

import os
import sys
import glob
import fontforge
import psMat

sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
from fontmetrics import lock_metrics
from ranges import NF_RANGES, OVERFLOW_RANGES
import pins as pins_mod

if len(sys.argv) < 4:
    print("Usage: fontforge -script merge-new-octicons.py <patched.ttf> <upstream-octicons-dir/> <output.ttf>")
    sys.exit(1)

patched_path = sys.argv[1]
upstream_dir = sys.argv[2]
output_path = sys.argv[3]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
PINS_PATH = os.path.join(REPO_ROOT, "glyphs", "octicons-pins.json")

target = fontforge.open(patched_path)

cell_width = None
for glyph in target.glyphs():
    if glyph.width > 0:
        cell_width = glyph.width
        break
if cell_width is None:
    cell_width = target.em

nf_oct_path = os.path.join(REPO_ROOT, "vendor", "src", "glyphs", "octicons", "octicons.otf")
if not os.path.exists(nf_oct_path):
    nf_oct_path = "vendor/src/glyphs/octicons/octicons.otf"

print(f"Loading NF-bundled Octicons from: {nf_oct_path}")
nf_oct = fontforge.open(nf_oct_path)
nf_glyph_names = set()
for glyph in nf_oct.glyphs():
    if glyph.isWorthOutputting():
        nf_glyph_names.add(glyph.glyphname)
print(f"NF-bundled Octicons has {len(nf_glyph_names)} glyphs")
nf_oct.close()

pins = pins_mod.load(PINS_PATH)
print(f"Loaded {len(pins)} Octicons pins")

oct_primary_end = NF_RANGES["Octicons"][1]
oct_overflow_start, oct_overflow_end = OVERFLOW_RANGES["Octicons"]

last_nf_oct_cp = 0xF400
for codepoint in range(0xF400, 0xFA11):
    try:
        g = target[codepoint]
        if g.isWorthOutputting():
            last_nf_oct_cp = codepoint
    except TypeError:
        pass

next_cp = last_nf_oct_cp + 1
print(f"Last NF Octicons codepoint: U+{last_nf_oct_cp:04X}, next sequential from U+{next_cp:04X}")

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
icons = {}
for svg_path in all_svgs:
    basename = os.path.splitext(os.path.basename(svg_path))[0]
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
        if size == 16 or (existing_size != 16 and size < existing_size):
            icons[name] = (size, svg_path)

print(f"Unique icon names: {len(icons)}")

# Collect new icons (not in NF-bundled)
new_icons = {name: svg_path for name, (_, svg_path) in icons.items()
             if name not in nf_glyph_names}


def find_next_free_cp():
    global next_cp
    while True:
        if next_cp > oct_primary_end and next_cp < oct_overflow_start:
            print(f"Primary Octicons range full, switching to overflow at U+{oct_overflow_start:05X}")
            next_cp = oct_overflow_start
        if next_cp > oct_overflow_end:
            print(f"ERROR: Octicons overflow range exhausted at U+{oct_overflow_end:05X}")
            sys.exit(1)
        try:
            if target[next_cp].isWorthOutputting():
                next_cp += 1
                continue
        except TypeError:
            pass
        break


def import_and_place(name, svg_path, placed_cp):
    glyph = target.createChar(placed_cp, name)
    glyph.importOutlines(svg_path)

    bbox = glyph.boundingBox()
    if bbox[2] - bbox[0] > 0 and bbox[3] - bbox[1] > 0:
        scale = target.em * 0.9 / max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        glyph.transform(psMat.scale(scale))

        bbox = glyph.boundingBox()
        x_offset = (cell_width - (bbox[2] - bbox[0])) / 2.0 - bbox[0]
        target_mid = (target.ascent - target.descent) / 2.0
        glyph_mid = (bbox[1] + bbox[3]) / 2.0
        glyph.transform(psMat.translate(x_offset, target_mid - glyph_mid))

    glyph.width = cell_width


pinned_names = {n: pins[n] for n in new_icons if n in pins}
truly_new = sorted(n for n in new_icons if n not in pins)
print(f"Found {len(new_icons)} new Octicons ({len(pinned_names)} pinned, {len(truly_new)} new)")

# Pass 1: place pinned glyphs
for name, placed_cp in sorted(pinned_names.items(), key=lambda x: x[1]):
    import_and_place(name, new_icons[name], placed_cp)
    print(f"  Pinned  U+{placed_cp:05X}: {name}")

print(f"  Placed {len(pinned_names)} pinned Octicons glyphs")

# Pass 2: place new glyphs sequentially
count_new = 0
for name in truly_new:
    find_next_free_cp()
    placed_cp = next_cp
    import_and_place(name, new_icons[name], placed_cp)
    pins[name] = placed_cp
    next_cp += 1
    count_new += 1
    print(f"  New     U+{placed_cp:05X}: {name}")

pins_mod.save(PINS_PATH, pins)
print(f"Saved {len(pins)} pins to {PINS_PATH}")
print(f"Merged {len(pinned_names) + count_new} new Octicons glyphs")

target.fontname = "LowGravitasSymbols"
target.familyname = "Low Gravitas Symbols"
target.fullname = "Low Gravitas Symbols"

lock_metrics(target)
target.generate(output_path)
print(f"Saved to {output_path}")
