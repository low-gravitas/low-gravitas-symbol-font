#!/usr/bin/env python3
"""Compare two glyphs.json manifests and report additions, removals, and renames.

Usage:
  python3 scripts/diff-glyphs.py <old.json> <new.json> [options]

Options:
  --format text|markdown|json   Output format (default: text)
  --from-version VERSION        Tag name for the old manifest (for JSON/markdown output)
  --to-version VERSION          Tag name for the new manifest (for JSON/markdown output)
  --max-rows N                  Max table rows per section in markdown (default: 50)
"""

import json
import sys


def load(path):
    with open(path) as f:
        data = json.load(f)
    return {g["cp"]: g for g in data}


def diff(old, new):
    old_cps = set(old)
    new_cps = set(new)

    added = [new[cp] for cp in sorted(new_cps - old_cps)]
    removed = [old[cp] for cp in sorted(old_cps - new_cps)]
    renamed = [
        (old[cp], new[cp])
        for cp in sorted(old_cps & new_cps)
        if old[cp]["name"] != new[cp]["name"]
    ]

    return added, removed, renamed


def fmt_glyph(g):
    return f"U+{g['hex']}  {g['name']}  ({g['set']})"


def fmt_rename(old_g, new_g):
    return f"U+{old_g['hex']}  {old_g['name']} → {new_g['name']}  ({old_g['set']})"


def report_text(added, removed, renamed, old_path, new_path):
    lines = [f"Glyph diff: {old_path} → {new_path}", ""]

    if not added and not removed and not renamed:
        lines.append("No glyph changes.")
        return "\n".join(lines)

    if added:
        lines.append(f"Added ({len(added)}):")
        for g in added:
            lines.append(f"  + {fmt_glyph(g)}")
        lines.append("")

    if removed:
        lines.append(f"Removed ({len(removed)}):")
        for g in removed:
            lines.append(f"  - {fmt_glyph(g)}")
        lines.append("")

    if renamed:
        lines.append(f"Renamed ({len(renamed)}):")
        for old_g, new_g in renamed:
            lines.append(f"  ~ {fmt_rename(old_g, new_g)}")
        lines.append("")

    return "\n".join(lines)


def report_markdown(added, removed, renamed, from_ver=None, to_ver=None, max_rows=50):
    lines = []

    if not added and not removed and not renamed:
        lines.append("No glyph changes in this release.")
        return "\n".join(lines)

    lines.append("### Glyph changes")
    lines.append("")

    def table_section(title, rows, cols, row_fn):
        lines.append(f"**{title} ({len(rows)})**")
        lines.append("")
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("| " + " | ".join("---" for _ in cols) + " |")
        for row in rows[:max_rows]:
            lines.append("| " + " | ".join(row_fn(row)) + " |")
        if len(rows) > max_rows:
            lines.append(f"| *… and {len(rows) - max_rows} more* | | |")
        lines.append("")

    if added:
        table_section(
            f"Added", added,
            ["Codepoint", "Name", "Set"],
            lambda g: [f"U+{g['hex']}", f"`{g['name']}`", g["set"]],
        )

    if removed:
        table_section(
            f"Removed", removed,
            ["Codepoint", "Name", "Set"],
            lambda g: [f"U+{g['hex']}", f"`{g['name']}`", g["set"]],
        )

    if renamed:
        table_section(
            f"Renamed", renamed,
            ["Codepoint", "Old name", "New name"],
            lambda r: [f"U+{r[0]['hex']}", f"`{r[0]['name']}`", f"`{r[1]['name']}`"],
        )

    return "\n".join(lines)


def report_json(added, removed, renamed, from_ver=None, to_ver=None):
    out = {
        "from": from_ver,
        "to": to_ver,
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "renamed": len(renamed),
        },
        "added": [
            {"cp": g["cp"], "hex": g["hex"], "name": g["name"], "set": g["set"]}
            for g in added
        ],
        "removed": [
            {"cp": g["cp"], "hex": g["hex"], "name": g["name"], "set": g["set"]}
            for g in removed
        ],
        "renamed": [
            {
                "cp": o["cp"],
                "hex": o["hex"],
                "old_name": o["name"],
                "new_name": n["name"],
                "set": o["set"],
            }
            for o, n in renamed
        ],
    }
    return json.dumps(out, indent=2)


def parse_args(args):
    fmt = "text"
    from_ver = None
    to_ver = None
    max_rows = 50
    positional = []

    i = 0
    while i < len(args):
        if args[i] == "--format":
            fmt = args[i + 1]; i += 2
        elif args[i] == "--from-version":
            from_ver = args[i + 1]; i += 2
        elif args[i] == "--to-version":
            to_ver = args[i + 1]; i += 2
        elif args[i] == "--max-rows":
            max_rows = int(args[i + 1]); i += 2
        else:
            positional.append(args[i]); i += 1

    return fmt, from_ver, to_ver, max_rows, positional


def main():
    fmt, from_ver, to_ver, max_rows, positional = parse_args(sys.argv[1:])

    if len(positional) != 2:
        print("Usage: diff-glyphs.py <old.json> <new.json> [--format text|markdown|json] "
              "[--from-version V] [--to-version V] [--max-rows N]")
        sys.exit(1)

    old = load(positional[0])
    new = load(positional[1])
    added, removed, renamed = diff(old, new)

    if fmt == "json":
        print(report_json(added, removed, renamed, from_ver, to_ver))
    elif fmt == "markdown":
        print(report_markdown(added, removed, renamed, from_ver, to_ver, max_rows))
    else:
        print(report_text(added, removed, renamed, positional[0], positional[1]))


if __name__ == "__main__":
    main()
