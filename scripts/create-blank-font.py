#!/usr/bin/env fontforge -script
"""Create an empty base font for font-patcher's symbolsonly mode."""

import fontforge

font = fontforge.font()

font.fontname = "LowGravitasSymbols"
font.familyname = "Low Gravitas Symbols"
font.fullname = "Low Gravitas Symbols"
font.em = 2048
font.ascent = 1638
font.descent = 410
font.encoding = "UnicodeFull"

# Typical monospace cell width: ~60% of em (matches JetBrains Mono proportions).
# This ratio affects how font-patcher scales and places symbols.
CELL_WIDTH = 1230

# Set explicit vertical metrics with zero linegap.
# Without this, FontForge auto-generates a linegap (~184 units) which the
# font-patcher redistributes into ascent/descent, inflating the effective
# height and causing all symbols to be scaled down to ~82% of correct size.
font.hhea_ascent = font.ascent
font.hhea_descent = -font.descent
font.hhea_linegap = 0
font.os2_typoascent = font.ascent
font.os2_typodescent = -font.descent
font.os2_typolinegap = 0
font.os2_winascent = font.ascent
font.os2_windescent = font.descent
font.os2_use_typo_metrics = 1

# Add a dummy .notdef glyph (required for valid font)
glyph = font.createChar(-1, ".notdef")
pen = glyph.glyphPen()
pen.moveTo((0, 0))
pen.lineTo((0, font.ascent))
pen.lineTo((CELL_WIDTH, font.ascent))
pen.lineTo((CELL_WIDTH, 0))
pen.closePath()
pen = None
glyph.width = CELL_WIDTH

# Add a space glyph and a dummy 'X' glyph so font-patcher can detect sane dimensions.
# The patcher scans U+0021-017F for advance widths — space alone (U+0020) is outside that range.
# The X glyph must span the full ascent-to-descent range so font-patcher scales symbols correctly.
space = font.createChar(0x20, "space")
space.width = CELL_WIDTH

dummy = font.createChar(0x58, "X")
pen = dummy.glyphPen()
pen.moveTo((0, -font.descent))
pen.lineTo((0, font.ascent))
pen.lineTo((CELL_WIDTH, font.ascent))
pen.lineTo((CELL_WIDTH, -font.descent))
pen.closePath()
pen = None
dummy.width = CELL_WIDTH

font.generate("build/blank-base.ttf")
print("Created build/blank-base.ttf")
