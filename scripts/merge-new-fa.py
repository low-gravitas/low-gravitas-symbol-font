#!/usr/bin/env fontforge -script
"""Merge newer Font Awesome glyphs not present in the Nerd Fonts build.

Codepoint assignment strategy:
- Glyphs previously assigned a codepoint are recorded in glyphs/fa-pins.json.
  On each build those glyphs are placed at their pinned codepoints (pass 1), so
  upstream renames or reorderings never shift existing assignments.
- Truly new glyph names are placed sequentially in pass 2, starting after the
  last used NF FA codepoint (U+ED00+) or into overflow (U+F1B00+).
  All placements are added to the pins file for future stability.
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
    print("Usage: fontforge -script merge-new-fa.py <patched.ttf> <upstream-fa-dir/> <output.ttf>")
    sys.exit(1)

patched_path = sys.argv[1]
upstream_dir = sys.argv[2]
output_path = sys.argv[3]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
PINS_PATH = os.path.join(REPO_ROOT, "glyphs", "fa-pins.json")

target = fontforge.open(patched_path)

cell_width = None
for glyph in target.glyphs():
    if glyph.width > 0:
        cell_width = glyph.width
        break
if cell_width is None:
    cell_width = target.em

nf_fa_path = os.path.join(REPO_ROOT, "vendor", "src", "glyphs", "font-awesome", "FontAwesome.otf")
if not os.path.exists(nf_fa_path):
    nf_fa_path = "vendor/src/glyphs/font-awesome/FontAwesome.otf"

print(f"Loading NF-bundled FA from: {nf_fa_path}")
nf_fa = fontforge.open(nf_fa_path)
nf_glyph_names = set()
for glyph in nf_fa.glyphs():
    if glyph.isWorthOutputting():
        nf_glyph_names.add(glyph.glyphname)
print(f"NF-bundled FA has {len(nf_glyph_names)} glyphs")
nf_fa.close()

pins = pins_mod.load(PINS_PATH)
print(f"Loaded {len(pins)} FA pins")

fa_primary_end = NF_RANGES["Font Awesome"][1]
fa_overflow_start, fa_overflow_end = OVERFLOW_RANGES["Font Awesome"]

last_nf_fa_cp = 0xED00
for codepoint in range(0xED00, 0xF300):
    try:
        g = target[codepoint]
        if g.isWorthOutputting():
            last_nf_fa_cp = codepoint
    except TypeError:
        pass

next_cp = last_nf_fa_cp + 1
print(f"Last NF FA codepoint: U+{last_nf_fa_cp:04X}, next sequential from U+{next_cp:04X}")

upstream_otfs = glob.glob(os.path.join(upstream_dir, "**", "*.otf"), recursive=True)
if not upstream_otfs:
    print("No upstream FA OTF files found, skipping FA merge")
    lock_metrics(target)
    target.generate(output_path)
    sys.exit(0)

print(f"Found upstream FA fonts: {upstream_otfs}")


def find_next_free_cp():
    global next_cp
    while True:
        if next_cp > fa_primary_end and next_cp < fa_overflow_start:
            print(f"Primary FA range full, switching to overflow at U+{fa_overflow_start:05X}")
            next_cp = fa_overflow_start
        if next_cp > fa_overflow_end:
            print(f"ERROR: Font Awesome overflow range exhausted at U+{fa_overflow_end:05X}")
            sys.exit(1)
        try:
            if target[next_cp].isWorthOutputting():
                next_cp += 1
                continue
        except TypeError:
            pass
        break


def copy_and_place(source, glyphname, placed_cp, scale_factor):
    source.selection.select(glyphname)
    source.copy()
    target.createChar(placed_cp, glyphname)
    target.selection.select(placed_cp)
    target.paste()

    g = target[placed_cp]
    if scale_factor != 1.0:
        g.transform(psMat.scale(scale_factor))

    bbox = g.boundingBox()
    gw = bbox[2] - bbox[0]
    gh = bbox[3] - bbox[1]
    if gw > 0 and gh > 0:
        fill_scale = target.em * 0.9 / max(gw, gh)
        g.transform(psMat.scale(fill_scale))
        bbox = g.boundingBox()
        x_off = (cell_width - (bbox[2] - bbox[0])) / 2.0 - bbox[0]
        target_mid = (target.ascent - target.descent) / 2.0
        glyph_mid = (bbox[1] + bbox[3]) / 2.0
        g.transform(psMat.translate(x_off, target_mid - glyph_mid))

    g.width = cell_width


# Collection phase: gather {name -> (file_path, scale_factor)} for all new glyphs.
# First-seen file wins when a name appears in multiple FA variant fonts.
glyph_sources = {}
for otf_path in sorted(upstream_otfs):
    source = fontforge.open(otf_path)
    sf = target.em / source.em if target.em != source.em else 1.0
    for glyph in source.glyphs():
        if not glyph.isWorthOutputting():
            continue
        if glyph.glyphname in nf_glyph_names:
            continue
        if glyph.glyphname.startswith("."):
            continue
        if glyph.glyphname not in glyph_sources:
            glyph_sources[glyph.glyphname] = (otf_path, sf)
    source.close()

pinned_names = {n: pins[n] for n in glyph_sources if n in pins}
new_names = sorted(n for n in glyph_sources if n not in pins)
print(f"Found {len(glyph_sources)} new FA glyphs ({len(pinned_names)} pinned, {len(new_names)} new)")

# Pass 1: place pinned glyphs (grouped by source file to minimise font opens)
by_file = {}
for name, placed_cp in sorted(pinned_names.items(), key=lambda x: x[1]):
    otf_path, sf = glyph_sources[name]
    by_file.setdefault(otf_path, []).append((name, placed_cp, sf))

for otf_path in sorted(by_file.keys()):
    source = fontforge.open(otf_path)
    for name, placed_cp, sf in by_file[otf_path]:
        copy_and_place(source, name, placed_cp, sf)
        nf_glyph_names.add(name)
    source.close()

print(f"  Placed {len(pinned_names)} pinned FA glyphs")

# Pass 2: place new glyphs sequentially (grouped by source file)
new_by_file = {}
for name in new_names:
    otf_path, sf = glyph_sources[name]
    new_by_file.setdefault(otf_path, []).append((name, sf))

count_new = 0
for otf_path in sorted(new_by_file.keys()):
    source = fontforge.open(otf_path)
    for name, sf in sorted(new_by_file[otf_path]):
        find_next_free_cp()
        placed_cp = next_cp
        copy_and_place(source, name, placed_cp, sf)
        pins[name] = placed_cp
        nf_glyph_names.add(name)
        next_cp += 1
        count_new += 1
        print(f"  New     U+{placed_cp:05X}: {name}")
    source.close()

pins_mod.save(PINS_PATH, pins)
print(f"Saved {len(pins)} pins to {PINS_PATH}")
print(f"Merged {len(pinned_names) + count_new} new Font Awesome glyphs")

target.fontname = "LowGravitasSymbols"
target.familyname = "Low Gravitas Symbols"
target.fullname = "Low Gravitas Symbols"

lock_metrics(target)
target.generate(output_path)
print(f"Saved to {output_path}")
