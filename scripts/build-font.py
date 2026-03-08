#!/usr/bin/env fontforge -script
"""Build LowGravitasSymbols font by directly merging glyphs from NF source fonts.

Bypasses font-patcher entirely — copies glyphs from each source font, scales them
to fill the em square, remaps codepoints per the Nerd Fonts mapping, and centers
them within the cell.
"""

import os
import sys
import glob
import fontforge
import psMat

sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
from fontmetrics import lock_metrics

# ---------------------------------------------------------------------------
# Glyph set definitions — derived from font-patcher's patch set table
# Each entry: (name, filename, src_start, src_end, dst_start, exact)
#   exact=True:  codepoints are preserved (dst = src)
#   exact=False: codepoints are remapped (dst_start + offset from src_start)
# ---------------------------------------------------------------------------
# Field meanings (matching font-patcher's naming, which is confusing):
#   src_start/src_end: codepoint range to SELECT in the source font
#   dst_start: codepoint to START WRITING at in the target font
#     None = same as src_start (exact mapping)
#   exact: True = preserve source codepoints, False = pack sequentially from dst_start
GLYPH_SETS = [
    # Seti-UI + Custom (source E4FA-E5B8 -> dest E5FA+, packed)
    ("Seti-UI + Custom",        "original-source.otf",                          0xE4FA, 0xE5B8, 0xE5FA, False),
    # Heavy Angle Brackets
    ("Heavy Angle Brackets",    "extraglyphs.sfd",                              0x276C, 0x2771, None, True),
    # Box Drawing
    ("Box Drawing",             "extraglyphs.sfd",                              0x2500, 0x259F, None, True),
    # Progress Indicators
    ("Progress Indicators",     "extraglyphs.sfd",                              0xEE00, 0xEE0B, None, True),
    # Devicons (source E600-E7EF -> dest E700+, packed)
    ("Devicons",                "devicons/devicons.otf",                        0xE600, 0xE7EF, 0xE700, False),
    # Powerline Symbols
    ("Powerline Symbols",       "powerline-symbols/PowerlineSymbols.otf",       0xE0A0, 0xE0A2, None, True),
    ("Powerline Symbols",       "powerline-symbols/PowerlineSymbols.otf",       0xE0B0, 0xE0B3, None, True),
    # Powerline Extra Symbols
    ("Powerline Extra",         "powerline-extra/PowerlineExtraSymbols.otf",    0xE0A3, 0xE0A3, None, True),
    ("Powerline Extra",         "powerline-extra/PowerlineExtraSymbols.otf",    0xE0B4, 0xE0C8, None, True),
    ("Powerline Extra",         "powerline-extra/PowerlineExtraSymbols.otf",    0xE0CA, 0xE0CA, None, True),
    ("Powerline Extra",         "powerline-extra/PowerlineExtraSymbols.otf",    0xE0CC, 0xE0D7, None, True),
    # Pomicons
    ("Pomicons",                "pomicons/Pomicons.otf",                        0xE000, 0xE00A, None, True),
    # Font Awesome (source has these at ED00-F2FF natively)
    ("Font Awesome",            "font-awesome/FontAwesome.otf",                 0xED00, 0xF2FF, None, True),
    # Font Awesome Extension (source E000-E0A9 -> dest E200+, packed)
    ("Font Awesome Extension",  "font-awesome-extension.ttf",                   0xE000, 0xE0A9, 0xE200, False),
    # Weather Icons (source F000-F0EB -> dest E300+, packed)
    ("Weather Icons",           "weather-icons/weathericons-regular-webfont.ttf", 0xF000, 0xF0EB, 0xE300, False),
    # Font Logos
    ("Font Logos",              "font-logos.ttf",                                0xF300, 0xF381, None, True),
    # Octicons (source F000-F105 -> dest F400+, packed)
    ("Octicons",                "octicons/octicons.otf",                        0xF000, 0xF105, 0xF400, False),
    # Octicons extra (source F27C-F306 -> dest F4A9+, packed)
    ("Octicons",                "octicons/octicons.otf",                        0xF27C, 0xF306, 0xF4A9, False),
    # Octicons specials (exact)
    ("Octicons",                "octicons/octicons.otf",                        0x2665, 0x2665, None, True),
    ("Octicons",                "octicons/octicons.otf",                        0x26A1, 0x26A1, None, True),
    # Codicons
    ("Codicons",                "codicons/codicon.ttf",                         0xEA60, 0xEC1E, None, True),
    # Material Design Icons
    ("Material Design",         "materialdesign/MaterialDesignIconsDesktop.ttf", 0xF0001, 0xF1AF0, None, True),
]


def copy_glyphs_direct(target, source, src_start, src_end, dst_start, exact, cell_width):
    """Copy glyphs from source font to target, scaling to fill the em square."""
    scale_factor = target.em / source.em if target.em != source.em else 1.0
    count = 0
    dst_cp = dst_start if dst_start is not None else src_start

    for src_cp in range(src_start, src_end + 1):
        try:
            src_glyph = source[src_cp]
            if not src_glyph.isWorthOutputting():
                if not exact:
                    pass  # don't increment dst for missing glyphs in packed mode
                continue
        except TypeError:
            if not exact:
                pass
            continue

        if exact:
            target_cp = src_cp
        else:
            target_cp = dst_cp
            dst_cp += 1

        # Skip if already occupied
        try:
            existing = target[target_cp]
            if existing.isWorthOutputting():
                if not exact:
                    pass  # already incremented
                continue
        except TypeError:
            pass

        source.selection.select(src_cp)
        source.copy()
        target.createChar(target_cp, src_glyph.glyphname)
        target.selection.select(target_cp)
        target.paste()

        g = target[target_cp]

        # Scale to target em (match em sizes between fonts)
        if scale_factor != 1.0:
            g.transform(psMat.scale(scale_factor))

        # Scale glyph to fill the em square (90% with padding)
        bbox = g.boundingBox()
        glyph_width = bbox[2] - bbox[0]
        glyph_height = bbox[3] - bbox[1]

        if glyph_width > 0 and glyph_height > 0:
            target_size = target.em * 0.9
            fill_scale = target_size / max(glyph_width, glyph_height)
            g.transform(psMat.scale(fill_scale))

            # Center horizontally within cell, vertically within em
            bbox = g.boundingBox()
            x_offset = (cell_width - (bbox[2] - bbox[0])) / 2.0 - bbox[0]
            target_mid = (target.ascent - target.descent) / 2.0
            glyph_mid = (bbox[1] + bbox[3]) / 2.0
            y_offset = target_mid - glyph_mid
            g.transform(psMat.translate(x_offset, y_offset))

        g.width = cell_width
        count += 1

    return count


def main():
    if len(sys.argv) < 3:
        print("Usage: fontforge -script build-font.py <glyphs-dir> <output.ttf>")
        sys.exit(1)

    glyphs_dir = sys.argv[1]
    output_path = sys.argv[2]

    # Create the base font
    font = fontforge.font()
    font.fontname = "LowGravitasSymbols"
    font.familyname = "Low Gravitas Symbols"
    font.fullname = "Low Gravitas Symbols"
    font.em = 2048
    font.ascent = 1638
    font.descent = 410
    font.encoding = "UnicodeFull"

    lock_metrics(font)

    # Cell width — roughly 60% of em for typical mono proportions
    cell_width = 1230

    # Add .notdef
    glyph = font.createChar(-1, ".notdef")
    pen = glyph.glyphPen()
    pen.moveTo((0, 0))
    pen.lineTo((0, font.ascent))
    pen.lineTo((cell_width, font.ascent))
    pen.lineTo((cell_width, 0))
    pen.closePath()
    pen = None
    glyph.width = cell_width

    # Add space
    space = font.createChar(0x20, "space")
    space.width = cell_width

    total = 0
    prev_filename = None
    source = None

    for name, filename, src_start, src_end, dst_start, exact in GLYPH_SETS:
        filepath = os.path.join(glyphs_dir, filename)
        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found, skipping {name}")
            continue

        if filename != prev_filename:
            if source is not None:
                source.close()
            source = fontforge.open(filepath)
            prev_filename = filename

        count = copy_glyphs_direct(font, source, src_start, src_end, dst_start, exact, cell_width)
        total += count
        dst_label = f"U+{dst_start:04X}+" if dst_start and not exact else "exact"
        print(f"  {name}: {count} glyphs (U+{src_start:04X}-{src_end:04X} -> {dst_label})")

    if source is not None:
        source.close()

    print(f"\nTotal: {total} glyphs from NF sources")

    font.generate(output_path)
    print(f"Saved to {output_path}")


if __name__ == '__main__':
    main()
