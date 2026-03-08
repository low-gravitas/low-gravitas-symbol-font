#!/bin/bash
set -euo pipefail

for cmd in curl jq unzip; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is not installed."
    echo "  brew install $cmd"
    exit 1
  fi
done

# Downloads latest upstream versions of Codicons, Font Awesome, and Octicons.

mkdir -p vendor/upstream-codicons vendor/upstream-fa vendor/upstream-octicons

echo "Downloading latest Codicons from npm..."
CODICONS_URL=$(curl -fsSL https://registry.npmjs.org/@vscode/codicons/latest | jq -r '.dist.tarball')
curl -fsSL "$CODICONS_URL" | tar xz -C vendor/upstream-codicons/ --strip-components=2 package/dist/codicon.ttf
echo "  -> vendor/upstream-codicons/codicon.ttf"

echo "Downloading latest Font Awesome 6 Free from GitHub..."
FA_VERSION=$(curl -fsSL https://api.github.com/repos/FortAwesome/Font-Awesome/releases/latest | jq -r '.tag_name')
curl -fsSL "https://github.com/FortAwesome/Font-Awesome/releases/download/${FA_VERSION}/fontawesome-free-${FA_VERSION}-desktop.zip" \
  -o /tmp/fa-desktop.zip
unzip -o /tmp/fa-desktop.zip -d vendor/upstream-fa/
rm -f /tmp/fa-desktop.zip
echo "  -> vendor/upstream-fa/ (version ${FA_VERSION})"

echo "Downloading latest Octicons SVGs from npm..."
OCTICONS_URL=$(curl -fsSL https://registry.npmjs.org/@primer/octicons/latest | jq -r '.dist.tarball')
curl -fsSL "$OCTICONS_URL" | tar xz -C vendor/upstream-octicons/
echo "  -> vendor/upstream-octicons/ (SVGs — will be compiled to font during build)"

echo "Done. Upstream fonts downloaded."
