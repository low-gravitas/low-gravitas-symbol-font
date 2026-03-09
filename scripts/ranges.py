"""Shared codepoint range definitions for the Low Gravitas Symbols font.

Single source of truth for NF-compatible ranges and overflow ranges.
Used by merge scripts and manifest generation.
"""

# Primary NF ranges (must match Nerd Fonts codepoint assignments)
NF_RANGES = {
    "Pomicons":               (0xE000,  0xE00A),
    "Powerline":              (0xE0A0,  0xE0D7),
    "Font Awesome Extension": (0xE200,  0xE2A9),
    "Weather Icons":          (0xE300,  0xE3EB),
    "Seti-UI + Custom":       (0xE5FA,  0xE6B8),
    "Devicons":               (0xE700,  0xE8EF),
    "Custom (Low Gravitas)":  (0xE900,  0xE9FF),
    "Codicons":               (0xEA60,  0xEC84),
    "Progress Indicators":    (0xEE00,  0xEE0B),
    "Font Awesome":           (0xED00,  0xF2FF),
    "Font Logos":             (0xF300,  0xF381),
    "Octicons":               (0xF400,  0xFA10),
    "Box Drawing":            (0x2500,  0x259F),
    "Heavy Angle Brackets":   (0x276C,  0x2771),
    "Material Design":        (0xF0001, 0xF1AF0),
}

# Overflow ranges in Supplementary PUA-A (after Material Design)
OVERFLOW_RANGES = {
    "Font Awesome":          (0xF1B00, 0xF2FFF),
    "Octicons":              (0xF3000, 0xF3FFF),
    "Custom (Low Gravitas)": (0xF4000, 0xF4FFF),
    "Codicons":              (0xF5000, 0xF5FFF),
}


def get_set_ranges():
    """Return a list of (start, end, name) tuples for manifest classification.

    Includes both primary NF ranges and overflow ranges so that overflow
    glyphs are classified under their original set name.
    """
    ranges = []
    for name, (start, end) in NF_RANGES.items():
        ranges.append((start, end, name))
    for name, (start, end) in OVERFLOW_RANGES.items():
        ranges.append((start, end, name))
    return ranges
