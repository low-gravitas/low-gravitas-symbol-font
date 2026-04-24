#!/usr/bin/env fontforge -script
"""Merge newer Codicons glyphs not present in the Nerd Fonts build.

Codepoint assignment strategy:
- Glyphs previously assigned a codepoint are recorded in glyphs/codicons-pins.json.
  On each build those glyphs are placed at their pinned codepoints (pass 1), so
  upstream renames or reorderings never shift existing assignments.
- Truly new glyph names (not yet in the pins file) are placed in pass 2:
  at their native Codicons codepoint if that slot is free in the primary NF range
  (U+EA60–U+EC84), otherwise sequentially in the overflow range (U+F5000+).
  Overflow placements are added to the pins file for future stability.
"""

import os
import sys
import fontforge
import psMat

sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
from fontmetrics import lock_metrics
from ranges import NF_RANGES, OVERFLOW_RANGES
import pins as pins_mod

if len(sys.argv) < 4:
    print("Usage: fontforge -script merge-new-codicons.py <patched.ttf> <upstream-codicon.ttf> <output.ttf>")
    sys.exit(1)

patched_path = sys.argv[1]
upstream_path = sys.argv[2]
output_path = sys.argv[3]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
PINS_PATH = os.path.join(REPO_ROOT, "glyphs", "codicons-pins.json")

target = fontforge.open(patched_path)
source = fontforge.open(upstream_path)

scale_factor = target.em / source.em if target.em != source.em else 1.0

cell_width = None
for glyph in target.glyphs():
    if glyph.width > 0:
        cell_width = glyph.width
        break
if cell_width is None:
    cell_width = target.em

print(f"Target em: {target.em}, Source em: {source.em}, Scale: {scale_factor}")
print(f"Cell width: {cell_width}")

nf_cod_path = os.path.join(REPO_ROOT, "vendor", "src", "glyphs", "codicons", "codicon.ttf")
if not os.path.exists(nf_cod_path):
    nf_cod_path = "vendor/src/glyphs/codicons/codicon.ttf"

print(f"Loading NF-bundled Codicons from: {nf_cod_path}")
nf_cod = fontforge.open(nf_cod_path)
nf_glyph_names = set()
for glyph in nf_cod.glyphs():
    if glyph.isWorthOutputting():
        nf_glyph_names.add(glyph.glyphname)
print(f"NF-bundled Codicons has {len(nf_glyph_names)} glyphs")
nf_cod.close()

pins = pins_mod.load(PINS_PATH)
print(f"Loaded {len(pins)} Codicons pins")

cod_primary_start, cod_primary_end = NF_RANGES["Codicons"]
cod_overflow_start, cod_overflow_end = OVERFLOW_RANGES["Codicons"]

last_nf_cod_cp = cod_primary_start
for codepoint in range(cod_primary_start, cod_primary_end + 1):
    try:
        g = target[codepoint]
        if g.isWorthOutputting():
            last_nf_cod_cp = codepoint
    except TypeError:
        pass

next_cp = last_nf_cod_cp + 1
in_overflow = False
print(f"Last NF Codicons codepoint: U+{last_nf_cod_cp:04X}, next sequential from U+{next_cp:04X}")


def find_next_free_cp():
    global next_cp, in_overflow
    while True:
        if not in_overflow and next_cp > cod_primary_end:
            print(f"Primary Codicons range full, switching to overflow at U+{cod_overflow_start:05X}")
            next_cp = cod_overflow_start
            in_overflow = True
        if in_overflow and next_cp > cod_overflow_end:
            print(f"ERROR: Codicons overflow range exhausted at U+{cod_overflow_end:05X}")
            sys.exit(1)
        try:
            if target[next_cp].isWorthOutputting():
                next_cp += 1
                continue
        except TypeError:
            pass
        break


def copy_and_place(glyphname, placed_cp):
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

pinned_count = sum(1 for _, n in new_glyphs if n in pins)
print(f"Found {len(new_glyphs)} new Codicons glyphs ({pinned_count} pinned, {len(new_glyphs) - pinned_count} new)")

# Pass 1: place pinned glyphs at their stable codepoints
for _, glyphname in sorted(new_glyphs):
    if glyphname not in pins:
        continue
    placed_cp = pins[glyphname]
    copy_and_place(glyphname, placed_cp)
    nf_glyph_names.add(glyphname)
    print(f"  Pinned  U+{placed_cp:05X}: {glyphname}")

# Pass 2: place new glyphs (native codepoint if free, else sequential overflow)
count_new = 0
for src_cp, glyphname in sorted(new_glyphs):
    if glyphname in pins:
        continue

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
        pins[glyphname] = placed_cp

    copy_and_place(glyphname, placed_cp)
    nf_glyph_names.add(glyphname)
    count_new += 1
    print(f"  New     U+{placed_cp:05X}: {glyphname}")

pins_mod.save(PINS_PATH, pins)
print(f"Saved {len(pins)} pins to {PINS_PATH}")
print(f"Merged {pinned_count + count_new} Codicons glyphs ({pinned_count} pinned, {count_new} new)")

source.close()

target.fontname = "LowGravitasSymbols"
target.familyname = "Low Gravitas Symbols"
target.fullname = "Low Gravitas Symbols"

lock_metrics(target)
target.generate(output_path)
print(f"Saved to {output_path}")
