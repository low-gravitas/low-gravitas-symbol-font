---
description: "Release a new version of the symbol font — refresh sources, build, version bump, tag, verify, and update the hub"
---

# Release Process for Low Gravitas Symbol Font

Follow these steps in order. Ask the user before proceeding past each major step. Read the current `VERSION` file at the start to know the current version.

## Step 1: Refresh upstream icon sources (optional)

Ask the user whether they want to refresh upstream sources before building.

If yes:
- Run `make -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font update`
- Check `git -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font diff --stat` to see what changed in `vendor/` and `glyphs/`
- Summarize any new or removed glyph files for the user — these will go in the changelog later

If no, skip to Step 2.

## Step 2: Build the font

Run `make -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font build`

Verify:
- The command exits successfully
- `dist/LowGravitasSymbols.ttf`, `dist/glyphs.json`, and `dist/low-gravitas-symbols.css` all exist
- Report the glyph count from `dist/glyphs.json` (count the top-level keys)

If the build fails, diagnose the error and help the user fix it before continuing.

## Step 3: Install and test locally

Run `make -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font install`

Verify:
- `~/Library/Fonts/LowGravitasSymbols.ttf` exists and its modification time is current

Tell the user to visually verify glyphs render correctly in their terminal or editor before continuing. Wait for confirmation.

## Step 4: Determine the new version

Read the current `VERSION` file. Ask the user what kind of release this is:
- **Patch** (bug fixes, glyph name corrections): bump `0.x.Y`
- **Minor** (new glyphs added, upstream source updates): bump `0.X.0`
- **Major** (removed glyphs, changed codepoints, breaking changes): bump `X.0.0`

Suggest the appropriate version based on the changes observed in earlier steps. Write the new version to the `VERSION` file after the user confirms.

## Step 5: Update CHANGELOG.md

Read `CHANGELOG.md`. Add a new release section directly below the `## [Unreleased]` section (keep the Unreleased section, but move its contents into the new version section). Use this format:

```
## [X.Y.Z] - YYYY-MM-DD
```

Document what changed — new glyphs, removed glyphs, fixed glyph names, updated upstream sources, build changes, etc. Use the Keep a Changelog categories: Added, Changed, Deprecated, Removed, Fixed, Security.

Show the user the proposed changelog entry and wait for confirmation before writing.

## Step 6: Commit

Stage the changed files:
```
git -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font add VERSION CHANGELOG.md
```

Also stage any other modified source files (e.g., updated files in `vendor/`, `glyphs/`, `scripts/`, `build.sh`). Do NOT stage `dist/` — it is gitignored.

Check `git -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font status` to confirm what will be committed.

Commit with the version as the message:
```
git -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font commit -m "vX.Y.Z"
```

Push the commit:
```
git -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font push
```

## Step 7: Create and push the release tag

Run `make -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font release`

This creates an annotated tag `vX.Y.Z` and pushes it to origin, which triggers the GitHub Actions release workflow.

## Step 8: Verify the release

Wait for the release workflow to complete. Check status:
```
gh -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font run list --limit 1
```

If the workflow is still running, wait and check again. Once complete, verify all three release assets are present:
```
gh -C /Users/mike/Code/lowgravitas/low-gravitas-symbol-font release view vX.Y.Z --json assets -q '.assets[].name'
```

Expected assets:
- `LowGravitasSymbols.ttf`
- `glyphs.json`
- `low-gravitas-symbols.css`

If any assets are missing or the workflow failed, help the user diagnose the issue.

## Step 9: Bump the hub

After the release is confirmed, remind the user to update the hub repo to pick up the new font artifacts:

```
cd /Users/mike/Code/lowgravitas/low-gravitas.github.io && node scripts/bump-upstream.mjs --font=vX.Y.Z
```

Then commit and push the updated `artifacts.json` and `artifacts.lock.json` in that repo.

Ask the user if they want to do this now or handle it separately.
