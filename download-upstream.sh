#!/bin/bash
set -euo pipefail

for cmd in curl gh jq unzip; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is not installed."
    echo "  brew install $cmd"
    exit 1
  fi
done

# Downloads latest upstream versions of Codicons, Font Awesome, and Octicons.

mkdir -p vendor/upstream-codicons vendor/upstream-fa vendor/upstream-octicons

echo "Downloading latest Codicons from GitHub Pages (built from main branch)..."
curl -fsSL "https://microsoft.github.io/vscode-codicons/dist/codicon.ttf" \
  -o vendor/upstream-codicons/codicon.ttf
echo "  -> vendor/upstream-codicons/codicon.ttf"

echo "Downloading latest Font Awesome Free from GitHub..."
FA_VERSION=$(gh release view --repo FortAwesome/Font-Awesome --json tagName -q '.tagName')
gh release download "$FA_VERSION" \
  --repo FortAwesome/Font-Awesome \
  --pattern "fontawesome-free-${FA_VERSION}-desktop.zip" \
  --dir /tmp/
unzip -o "/tmp/fontawesome-free-${FA_VERSION}-desktop.zip" -d vendor/upstream-fa/
rm -f "/tmp/fontawesome-free-${FA_VERSION}-desktop.zip"
echo "  -> vendor/upstream-fa/ (version ${FA_VERSION})"

echo "Downloading latest Octicons SVGs from npm..."
OCTICONS_META=$(curl -fsSL https://registry.npmjs.org/@primer/octicons/latest)
OCTICONS_VERSION=$(echo "$OCTICONS_META" | jq -r '.version')
OCTICONS_URL=$(echo "$OCTICONS_META" | jq -r '.dist.tarball')
curl -fsSL "$OCTICONS_URL" | tar xz -C vendor/upstream-octicons/
echo "  -> vendor/upstream-octicons/ (version ${OCTICONS_VERSION})"

echo "Writing sources manifest..."
jq -n \
  --arg fa "$FA_VERSION" \
  --arg oct "$OCTICONS_VERSION" \
  '{
    "codicons": {"ref": "main", "source": "microsoft.github.io/vscode-codicons"},
    "font-awesome": {"version": $fa, "source": "github.com/FortAwesome/Font-Awesome"},
    "octicons": {"version": $oct, "source": "npmjs.com/package/@primer/octicons"}
  }' > vendor/sources.json
echo "  -> vendor/sources.json"

echo "Done. Upstream fonts downloaded."
