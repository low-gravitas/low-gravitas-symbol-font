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
OCTICONS_URL=$(curl -fsSL https://registry.npmjs.org/@primer/octicons/latest | jq -r '.dist.tarball')
curl -fsSL "$OCTICONS_URL" | tar xz -C vendor/upstream-octicons/
echo "  -> vendor/upstream-octicons/ (SVGs — will be compiled to font during build)"

echo "Done. Upstream fonts downloaded."
