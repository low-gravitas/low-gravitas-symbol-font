"""Codepoint pin registry for stable glyph assignments across builds.

Each merge script maintains a JSON pins file under glyphs/ mapping
glyph name → codepoint. On each build the script loads the file first,
places pinned glyphs at their recorded codepoints, then assigns new
sequential codepoints only to genuinely new glyph names.

This prevents codepoint churn when upstream sources add, rename, or
reorder glyphs — previously-assigned codepoints stay stable.
"""

import json
import os


def load(path):
    """Return {name: int_codepoint}. Empty dict if the file does not exist."""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        raw = json.load(f)
    return {name: int(hex_str, 16) for name, hex_str in raw.items()}


def save(path, pins):
    """Write {name: HEX_STRING} sorted by codepoint."""
    ordered = sorted(pins.items(), key=lambda item: item[1])
    serialized = {name: f'{cp:05X}' for name, cp in ordered}
    with open(path, 'w') as f:
        json.dump(serialized, f, indent=2)
        f.write('\n')
