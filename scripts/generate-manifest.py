#!/usr/bin/env fontforge -script
"""Generate a JSON manifest of all glyphs in the built font.

Usage: fontforge -script scripts/generate-manifest.py dist/LowGravitasSymbols.ttf site/glyphs.json
"""

import json
import os
import sys
import fontforge

# Codepoint ranges to icon set names (destination ranges in the final font)
SET_RANGES = [
    (0xE000,  0xE00A,  "Pomicons"),
    (0xE0A0,  0xE0D7,  "Powerline"),
    (0xE200,  0xE2A9,  "Font Awesome Extension"),
    (0xE300,  0xE3EB,  "Weather Icons"),
    (0xE5FA,  0xE6B8,  "Seti-UI + Custom"),
    (0xE700,  0xE8EF,  "Devicons"),
    (0xE900,  0xE9FF,  "Custom (Low Gravitas)"),
    (0xEA60,  0xEC84,  "Codicons"),
    (0xED00,  0xF2FF,  "Font Awesome"),
    (0xEE00,  0xEE0B,  "Progress Indicators"),
    (0xF300,  0xF381,  "Font Logos"),
    (0xF400,  0xFA10,  "Octicons"),
    (0x2500,  0x259F,  "Box Drawing"),
    (0x276C,  0x2771,  "Heavy Angle Brackets"),
    (0xF0001, 0xF1AF0, "Material Design"),
]


# Short prefixes for CSS class names: lg-{prefix}-{name}
SET_PREFIXES = {
    "Pomicons": "pomicons",
    "Powerline": "pl",
    "Font Awesome Extension": "fae",
    "Weather Icons": "weather",
    "Seti-UI + Custom": "seti",
    "Devicons": "dev",
    "Custom (Low Gravitas)": "custom",
    "Codicons": "cod",
    "Font Awesome": "fa",
    "Progress Indicators": "progress",
    "Font Logos": "logos",
    "Octicons": "oct",
    "Box Drawing": "box",
    "Heavy Angle Brackets": "bracket",
    "Material Design": "md",
    "Other": "other",
}


def classify(cp):
    for start, end, name in SET_RANGES:
        if start <= cp <= end:
            return name
    return "Other"


def css_class(set_name, glyph_name):
    """Generate a CSS class name like lg-fa-home."""
    prefix = SET_PREFIXES.get(set_name, "other")
    # Normalize glyph name to a valid CSS class fragment
    slug = glyph_name.lower().replace("_", "-").replace(".", "-").replace(" ", "-")
    return f"lg-{prefix}-{slug}"


def main():
    if len(sys.argv) < 3:
        print("Usage: fontforge -script generate-manifest.py <font.ttf> <output.json>")
        sys.exit(1)

    font_path = sys.argv[1]
    output_path = sys.argv[2]

    font = fontforge.open(font_path)
    glyphs = []

    for glyph in font.glyphs():
        cp = glyph.unicode
        if cp < 0 or not glyph.isWorthOutputting():
            continue
        if cp == 0x20:  # skip space
            continue
        set_name = classify(cp)
        cls = css_class(set_name, glyph.glyphname)
        glyphs.append({
            "cp": cp,
            "hex": f"{cp:04X}" if cp <= 0xFFFF else f"{cp:05X}",
            "name": glyph.glyphname,
            "set": set_name,
            "class": cls,
        })

    glyphs.sort(key=lambda g: g["cp"])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(glyphs, f)

    # Generate CSS stylesheet
    css_path = os.path.join(os.path.dirname(output_path), "low-gravitas-symbols.css")
    with open(css_path, "w") as f:
        f.write("@font-face {\n")
        f.write("  font-family: 'LowGravitasSymbols';\n")
        f.write("  src: url('LowGravitasSymbols.ttf') format('truetype');\n")
        f.write("  font-display: swap;\n")
        f.write("}\n\n")
        f.write("[class^='lg-'],\n[class*=' lg-'] {\n")
        f.write("  font-family: 'LowGravitasSymbols';\n")
        f.write("  font-style: normal;\n")
        f.write("  font-weight: normal;\n")
        f.write("  font-variant: normal;\n")
        f.write("  text-transform: none;\n")
        f.write("  line-height: 1;\n")
        f.write("  -webkit-font-smoothing: antialiased;\n")
        f.write("  -moz-osx-font-smoothing: grayscale;\n")
        f.write("}\n\n")
        for g in glyphs:
            cp = g["cp"]
            if cp <= 0xFFFF:
                esc = f"\\{cp:04X}"
            else:
                esc = f"\\{cp:05X}"
            f.write(f".{g['class']}::before {{ content: \"{esc}\"; }}\n")

    print(f"Generated manifest: {len(glyphs)} glyphs -> {output_path}")
    print(f"Generated CSS: {len(glyphs)} classes -> {css_path}")
    font.close()


if __name__ == "__main__":
    main()
