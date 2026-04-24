#!/usr/bin/env python3
"""Update upstream font sources to latest pinned versions.

Reads sources.json for tracking config, fetches the latest version for each
upstream, checks license files against stored hashes (halts on any change),
downloads font files to vendor/, and writes an updated sources.lock.json.

Run this before cutting a release when you want to pull in upstream updates.
After running, review the glyph diff and update CHANGELOG.md before committing.

Usage:
  python3 scripts/update-upstreams.py [--accept-license-changes]
"""

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
SOURCES_JSON = ROOT / "sources.json"
LOCK_JSON = ROOT / "sources.lock.json"
VENDOR = ROOT / "vendor"

ACCEPT_LICENSE_CHANGES = "--accept-license-changes" in sys.argv


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url) as r:
        return r.read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch_bytes(url))


def npm_meta(package: str, tag_or_version: str) -> dict:
    return fetch_json(f"https://registry.npmjs.org/{package}/{tag_or_version}")


def npm_tarball_url(package: str, version: str) -> str:
    pkg_name = package.split("/")[-1]
    return f"https://registry.npmjs.org/{package}/-/{pkg_name}-{version}.tgz"


def extract_from_tarball(data: bytes, member: str) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        return tf.extractfile(member).read()


def gh_latest_tag(repo: str) -> str:
    result = subprocess.run(
        ["gh", "release", "view", "--repo", repo, "--json", "tagName", "-q", ".tagName"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def gh_download(repo: str, tag: str, pattern: str, dest: Path):
    subprocess.run(
        ["gh", "release", "download", tag, "--repo", repo,
         "--pattern", pattern, "--dir", str(dest), "--clobber"],
        check=True,
    )


def warn_license_changed(name: str, old_hash: str, new_hash: str):
    print(f"\n  {'='*60}")
    print(f"  LICENSE CHANGED: {name}")
    print(f"  {'='*60}")
    print(f"  Previous hash: {old_hash}")
    print(f"  Current hash:  {new_hash}")
    print(f"\n  You MUST review the new license before distributing this font.")
    print(f"  Once reviewed, re-run with --accept-license-changes to proceed.")


# ── Per-source fetch functions ─────────────────────────────────────────────

def fetch_codicons(config: dict, lock: dict, accept: bool) -> tuple[dict, bytes]:
    """Returns (new_lock_entry, ttf_bytes)."""
    meta = npm_meta(config["npm_package"], config["npm_tag"])
    version = meta["version"]
    license_id = meta.get("license", "unknown")
    tarball_data = fetch_bytes(npm_tarball_url(config["npm_package"], version))

    license_data = extract_from_tarball(tarball_data, config["license_file"])
    license_hash = sha256_bytes(license_data)

    old = lock.get("codicons", {})
    if old.get("license_hash") and old["license_hash"] != license_hash:
        warn_license_changed("Codicons", old["license_hash"], license_hash)
        if not accept:
            sys.exit(1)

    ttf_data = extract_from_tarball(tarball_data, config["font_file"])

    entry = {"version": version, "license": license_id, "license_hash": license_hash}
    return entry, ttf_data


def fetch_font_awesome(config: dict, lock: dict, accept: bool, tmp: Path) -> dict:
    """Downloads FA to vendor/, returns new lock entry."""
    tag = gh_latest_tag(config["github_repo"])
    version = tag  # FA uses bare version tags like "7.2.0"
    asset = config["asset_pattern"].format(version=version)
    license_path = config["license_file"].format(version=version)

    gh_download(config["github_repo"], tag, asset, tmp)
    zip_path = tmp / asset

    with zipfile.ZipFile(zip_path) as zf:
        license_data = zf.read(license_path)
        license_hash = sha256_bytes(license_data)

    old = lock.get("font-awesome", {})
    if old.get("license_hash") and old["license_hash"] != license_hash:
        warn_license_changed("Font Awesome", old["license_hash"], license_hash)
        if not accept:
            sys.exit(1)

    fa_dir = VENDOR / "upstream-fa"
    fa_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(fa_dir)

    entry = {
        "version": version,
        "license": "Font Awesome Free License",
        "license_hash": license_hash,
    }
    return entry


def fetch_octicons(config: dict, lock: dict, accept: bool) -> dict:
    """Downloads Octicons to vendor/, returns new lock entry."""
    meta = npm_meta(config["npm_package"], config["npm_tag"])
    version = meta["version"]
    license_id = meta.get("license", "unknown")
    tarball_url = meta["dist"]["tarball"]
    tarball_data = fetch_bytes(tarball_url)

    license_data = extract_from_tarball(tarball_data, config["license_file"])
    license_hash = sha256_bytes(license_data)

    old = lock.get("octicons", {})
    if old.get("license_hash") and old["license_hash"] != license_hash:
        warn_license_changed("Octicons", old["license_hash"], license_hash)
        if not accept:
            sys.exit(1)

    oct_dir = VENDOR / "upstream-octicons"
    oct_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(tarball_data)) as tf:
        tf.extractall(oct_dir)

    entry = {"version": version, "license": license_id, "license_hash": license_hash}
    return entry


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    config = json.loads(SOURCES_JSON.read_text())
    lock = json.loads(LOCK_JSON.read_text()) if LOCK_JSON.exists() else {}

    new_lock = {}
    changed = []

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # Codicons
        print("Checking Codicons...")
        entry, ttf_data = fetch_codicons(config["codicons"], lock, ACCEPT_LICENSE_CHANGES)
        new_lock["codicons"] = entry
        old_ver = lock.get("codicons", {}).get("version")
        if old_ver != entry["version"]:
            changed.append(f"  Codicons: {old_ver or 'none'} → {entry['version']}")
        cod_dir = VENDOR / "upstream-codicons"
        cod_dir.mkdir(parents=True, exist_ok=True)
        (cod_dir / "codicon.ttf").write_bytes(ttf_data)
        print(f"  {entry['version']} (license: {entry['license']})")

        # Font Awesome
        print("Checking Font Awesome...")
        entry = fetch_font_awesome(config["font-awesome"], lock, ACCEPT_LICENSE_CHANGES, tmp)
        new_lock["font-awesome"] = entry
        old_ver = lock.get("font-awesome", {}).get("version")
        if old_ver != entry["version"]:
            changed.append(f"  Font Awesome: {old_ver or 'none'} → {entry['version']}")
        print(f"  {entry['version']} (license: {entry['license']})")

        # Octicons
        print("Checking Octicons...")
        entry = fetch_octicons(config["octicons"], lock, ACCEPT_LICENSE_CHANGES)
        new_lock["octicons"] = entry
        old_ver = lock.get("octicons", {}).get("version")
        if old_ver != entry["version"]:
            changed.append(f"  Octicons: {old_ver or 'none'} → {entry['version']}")
        print(f"  {entry['version']} (license: {entry['license']})")

    LOCK_JSON.write_text(json.dumps(new_lock, indent=2) + "\n")

    print()
    if changed:
        print("Upstream versions updated:")
        for line in changed:
            print(line)
        print()
        print("Next steps:")
        print("  1. Run the build: make build")
        print("  2. Review glyph changes: python3 scripts/diff-glyphs.py \\")
        print("       --format text dist/glyphs.json <previous-glyphs.json>")
        print("  3. Update CHANGELOG.md")
        print("  4. Commit sources.lock.json and CHANGELOG.md")
        print("  5. Cut the release: make release")
    else:
        print("All upstreams are up to date. sources.lock.json unchanged.")


if __name__ == "__main__":
    main()
