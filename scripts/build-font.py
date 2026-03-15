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


# Glyphs whose source fonts only provide "uniXXXX" names.
# These are well-known symbols; names from Powerline spec and Nerd Fonts docs.
GLYPH_NAME_OVERRIDES = {
    # Powerline core
    0xE0A0: "branch",
    0xE0A1: "line-number",
    0xE0A2: "padlock",
    0xE0A3: "column-number",
    0xE0B0: "right-triangle-solid",
    0xE0B1: "right-triangle-thin",
    0xE0B2: "left-triangle-solid",
    0xE0B3: "left-triangle-thin",
    # Powerline Extra
    0xE0B4: "right-half-circle-solid",
    0xE0B5: "right-half-circle-thin",
    0xE0B6: "left-half-circle-solid",
    0xE0B7: "left-half-circle-thin",
    0xE0B8: "lower-left-triangle-solid",
    0xE0B9: "lower-left-triangle-thin",
    0xE0BA: "lower-right-triangle-solid",
    0xE0BB: "lower-right-triangle-thin",
    0xE0BC: "upper-left-triangle-solid",
    0xE0BD: "upper-left-triangle-thin",
    0xE0BE: "upper-right-triangle-solid",
    0xE0BF: "upper-right-triangle-thin",
    0xE0C0: "flame-thick",
    0xE0C1: "flame-thin",
    0xE0C2: "flame-thick-mirrored",
    0xE0C3: "flame-thin-mirrored",
    0xE0C4: "pixelated-squares-small",
    0xE0C5: "pixelated-squares-small-mirrored",
    0xE0C6: "pixelated-squares-big",
    0xE0C7: "pixelated-squares-big-mirrored",
    0xE0C8: "ice-waveform",
    0xE0CA: "ice-waveform-mirrored",
    0xE0CC: "honeycomb",
    0xE0CD: "honeycomb-outline",
    0xE0CE: "lego-separator",
    0xE0CF: "lego-separator-thin",
    0xE0D0: "lego-block-facing",
    0xE0D1: "lego-block-sideways",
    0xE0D2: "trapezoid-top-bottom",
    0xE0D4: "trapezoid-top-bottom-mirrored",
    0xE0D6: "right-hard-divider-inverse",
    0xE0D7: "left-hard-divider-inverse",
    # Weather Icons (source F000-F0EB -> dest E300+, packed)
    0xE300: "day-cloudy-gusts",
    0xE301: "day-cloudy-windy",
    0xE302: "day-cloudy",
    0xE303: "day-fog",
    0xE304: "day-hail",
    0xE305: "day-lightning",
    0xE306: "day-rain-mix",
    0xE307: "day-rain-wind",
    0xE308: "day-rain",
    0xE309: "day-showers",
    0xE30A: "day-snow",
    0xE30B: "day-sprinkle",
    0xE30C: "day-sunny-overcast",
    0xE30D: "day-sunny",
    0xE30E: "day-storm-showers",
    0xE30F: "day-thunderstorm",
    0xE310: "cloudy-gusts",
    0xE311: "cloudy-windy",
    0xE312: "cloudy",
    0xE313: "fog",
    0xE314: "hail",
    0xE315: "lightning",
    0xE316: "rain-mix",
    0xE317: "rain-wind",
    0xE318: "rain",
    0xE319: "showers",
    0xE31A: "snow",
    0xE31B: "sprinkle",
    0xE31C: "storm-showers",
    0xE31D: "thunderstorm",
    0xE31E: "windy",
    0xE31F: "night-alt-cloudy-gusts",
    0xE320: "night-alt-cloudy-windy",
    0xE321: "night-alt-hail",
    0xE322: "night-alt-lightning",
    0xE323: "night-alt-rain-mix",
    0xE324: "night-alt-rain-wind",
    0xE325: "night-alt-rain",
    0xE326: "night-alt-showers",
    0xE327: "night-alt-snow",
    0xE328: "night-alt-sprinkle",
    0xE329: "night-alt-storm-showers",
    0xE32A: "night-alt-thunderstorm",
    0xE32B: "night-clear",
    0xE32C: "night-cloudy-gusts",
    0xE32D: "night-cloudy-windy",
    0xE32E: "night-cloudy",
    0xE32F: "night-hail",
    0xE330: "night-lightning",
    0xE331: "night-rain-mix",
    0xE332: "night-rain-wind",
    0xE333: "night-rain",
    0xE334: "night-showers",
    0xE335: "night-snow",
    0xE336: "night-sprinkle",
    0xE337: "night-storm-showers",
    0xE338: "night-thunderstorm",
    0xE339: "celsius",
    0xE33A: "cloud-down",
    0xE33B: "cloud-refresh",
    0xE33C: "cloud-up",
    0xE33D: "cloud",
    0xE33E: "degrees",
    0xE33F: "direction-down-left",
    0xE340: "direction-down",
    0xE341: "fahrenheit",
    0xE342: "horizon-alt",
    0xE343: "horizon",
    0xE344: "direction-left",
    0xE345: "aliens",
    0xE346: "night-fog",
    0xE347: "refresh-alt",
    0xE348: "refresh",
    0xE349: "direction-right",
    0xE34A: "raindrops",
    0xE34B: "strong-wind",
    0xE34C: "sunrise",
    0xE34D: "sunset",
    0xE34E: "thermometer-exterior",
    0xE34F: "thermometer-internal",
    0xE350: "thermometer",
    0xE351: "tornado",
    0xE352: "direction-up-right",
    0xE353: "direction-up",
    0xE354: "wind-deg-354",
    0xE355: "wind-deg-355",
    0xE356: "wind-deg-356",
    0xE357: "wind-deg-357",
    0xE358: "wind-deg-358",
    0xE359: "wind-deg-359",
    0xE35A: "wind-deg-35a",
    0xE35B: "wind-deg-35b",
    0xE35C: "smoke",
    0xE35D: "dust",
    0xE35E: "snow-wind",
    0xE35F: "day-snow-wind",
    0xE360: "night-snow-wind",
    0xE361: "night-alt-snow-wind",
    0xE362: "day-sleet-storm",
    0xE363: "night-sleet-storm",
    0xE364: "night-alt-sleet-storm",
    0xE365: "day-snow-thunderstorm",
    0xE366: "night-snow-thunderstorm",
    0xE367: "night-alt-snow-thunderstorm",
    0xE368: "solar-eclipse",
    0xE369: "lunar-eclipse",
    0xE36A: "meteor",
    0xE36B: "hot",
    0xE36C: "hurricane",
    0xE36D: "smog",
    0xE36E: "alien",
    0xE36F: "snowflake-cold",
    0xE370: "stars",
    0xE371: "raindrop",
    0xE372: "barometer",
    0xE373: "humidity",
    0xE374: "na",
    0xE375: "flood",
    0xE376: "day-cloudy-high",
    0xE377: "night-alt-cloudy-high",
    0xE378: "night-cloudy-high",
    0xE379: "night-alt-partly-cloudy",
    0xE37A: "sandstorm",
    0xE37B: "night-partly-cloudy",
    0xE37C: "umbrella",
    0xE37D: "day-windy",
    0xE37E: "night-alt-cloudy",
    0xE37F: "direction-up-left",
    0xE380: "direction-down-right",
    0xE381: "time-12",
    0xE382: "time-1",
    0xE383: "time-2",
    0xE384: "time-3",
    0xE385: "time-4",
    0xE386: "time-5",
    0xE387: "time-6",
    0xE388: "time-7",
    0xE389: "time-8",
    0xE38A: "time-9",
    0xE38B: "time-10",
    0xE38C: "time-11",
    0xE38D: "moon-new",
    0xE38E: "moon-waxing-crescent-1",
    0xE38F: "moon-waxing-crescent-2",
    0xE390: "moon-waxing-crescent-3",
    0xE391: "moon-waxing-crescent-4",
    0xE392: "moon-waxing-crescent-5",
    0xE393: "moon-waxing-crescent-6",
    0xE394: "moon-first-quarter",
    0xE395: "moon-waxing-gibbous-1",
    0xE396: "moon-waxing-gibbous-2",
    0xE397: "moon-waxing-gibbous-3",
    0xE398: "moon-waxing-gibbous-4",
    0xE399: "moon-waxing-gibbous-5",
    0xE39A: "moon-waxing-gibbous-6",
    0xE39B: "moon-full",
    0xE39C: "moon-waning-gibbous-1",
    0xE39D: "moon-waning-gibbous-2",
    0xE39E: "moon-waning-gibbous-3",
    0xE39F: "moon-waning-gibbous-4",
    0xE3A0: "moon-waning-gibbous-5",
    0xE3A1: "moon-waning-gibbous-6",
    0xE3A2: "moon-third-quarter",
    0xE3A3: "moon-waning-crescent-1",
    0xE3A4: "moon-waning-crescent-2",
    0xE3A5: "moon-waning-crescent-3",
    0xE3A6: "moon-waning-crescent-4",
    0xE3A7: "moon-waning-crescent-5",
    0xE3A8: "moon-waning-crescent-6",
    0xE3A9: "wind-direction",
    0xE3AA: "day-sleet",
    0xE3AB: "night-sleet",
    0xE3AC: "night-alt-sleet",
    0xE3AD: "sleet",
    0xE3AE: "day-haze",
    0xE3AF: "wind-beaufort-0",
    0xE3B0: "wind-beaufort-1",
    0xE3B1: "wind-beaufort-2",
    0xE3B2: "wind-beaufort-3",
    0xE3B3: "wind-beaufort-4",
    0xE3B4: "wind-beaufort-5",
    0xE3B5: "wind-beaufort-6",
    0xE3B6: "wind-beaufort-7",
    0xE3B7: "wind-beaufort-8",
    0xE3B8: "wind-beaufort-9",
    0xE3B9: "wind-beaufort-10",
    0xE3BA: "wind-beaufort-11",
    0xE3BB: "wind-beaufort-12",
    0xE3BC: "day-light-wind",
    0xE3BD: "tsunami",
    0xE3BE: "earthquake",
    0xE3BF: "fire",
    0xE3C0: "volcano",
    0xE3C1: "moonrise",
    0xE3C2: "moonset",
    0xE3C3: "train",
    0xE3C4: "small-craft-advisory",
    0xE3C5: "gale-warning",
    0xE3C6: "storm-warning",
    0xE3C7: "hurricane-warning",
    0xE3C8: "moon-alt-waxing-crescent-1",
    0xE3C9: "moon-alt-waxing-crescent-2",
    0xE3CA: "moon-alt-waxing-crescent-3",
    0xE3CB: "moon-alt-waxing-crescent-4",
    0xE3CC: "moon-alt-waxing-crescent-5",
    0xE3CD: "moon-alt-waxing-crescent-6",
    0xE3CE: "moon-alt-first-quarter",
    0xE3CF: "moon-alt-waxing-gibbous-1",
    0xE3D0: "moon-alt-waxing-gibbous-2",
    0xE3D1: "moon-alt-waxing-gibbous-3",
    0xE3D2: "moon-alt-waxing-gibbous-4",
    0xE3D3: "moon-alt-waxing-gibbous-5",
    0xE3D4: "moon-alt-waxing-gibbous-6",
    0xE3D5: "moon-alt-full",
    0xE3D6: "moon-alt-waning-gibbous-1",
    0xE3D7: "moon-alt-waning-gibbous-2",
    0xE3D8: "moon-alt-waning-gibbous-3",
    0xE3D9: "moon-alt-waning-gibbous-4",
    0xE3DA: "moon-alt-waning-gibbous-5",
    0xE3DB: "moon-alt-waning-gibbous-6",
    0xE3DC: "moon-alt-third-quarter",
    0xE3DD: "moon-alt-waning-crescent-1",
    0xE3DE: "moon-alt-waning-crescent-2",
    0xE3DF: "moon-alt-waning-crescent-3",
    0xE3E0: "moon-alt-waning-crescent-4",
    0xE3E1: "moon-alt-waning-crescent-5",
    0xE3E2: "moon-alt-waning-crescent-6",
    0xE3E3: "moon-alt-new",
    # Progress Indicators
    0xEE00: "progress-0",
    0xEE01: "progress-1",
    0xEE02: "progress-2",
    0xEE03: "progress-3",
    0xEE04: "progress-4",
    0xEE05: "progress-5",
    0xEE06: "progress-6",
    0xEE07: "progress-7",
    0xEE08: "progress-8",
    0xEE09: "progress-9",
    0xEE0A: "progress-10",
    0xEE0B: "progress-11",
}


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

    # Apply human-readable name overrides
    renamed = 0
    for cp, name in GLYPH_NAME_OVERRIDES.items():
        try:
            g = font[cp]
            if g.isWorthOutputting():
                g.glyphname = name
                renamed += 1
        except TypeError:
            pass
    print(f"Renamed {renamed} glyphs with readable names")

    font.generate(output_path)
    print(f"Saved to {output_path}")


if __name__ == '__main__':
    main()
