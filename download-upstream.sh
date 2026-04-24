#!/bin/bash
# Downloads upstream fonts at the exact versions pinned in sources.lock.json.
# For updating to newer versions, use: python3 scripts/update-upstreams.py
set -euo pipefail

for cmd in curl gh jq unzip; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is not installed."
    echo "  brew install $cmd"
    exit 1
  fi
done

if [ ! -f sources.lock.json ]; then
  echo "ERROR: sources.lock.json not found."
  echo "  Run 'python3 scripts/update-upstreams.py' to generate it."
  exit 1
fi

CODICONS_VERSION=$(jq -r '.codicons.version' sources.lock.json)
FA_VERSION=$(jq -r '."font-awesome".version' sources.lock.json)
OCTICONS_VERSION=$(jq -r '.octicons.version' sources.lock.json)

mkdir -p vendor/upstream-codicons vendor/upstream-fa vendor/upstream-octicons

echo "Downloading Codicons ${CODICONS_VERSION} from npm..."
PKG_NAME="codicons-${CODICONS_VERSION}.tgz"
curl -fsSL \
  "https://registry.npmjs.org/@vscode/codicons/-/${PKG_NAME}" \
  | tar xzf - -O package/dist/codicon.ttf \
  > vendor/upstream-codicons/codicon.ttf
echo "  -> vendor/upstream-codicons/codicon.ttf"

echo "Downloading Font Awesome ${FA_VERSION} from GitHub..."
gh release download "$FA_VERSION" \
  --repo FortAwesome/Font-Awesome \
  --pattern "fontawesome-free-${FA_VERSION}-desktop.zip" \
  --dir /tmp/ --clobber
unzip -o "/tmp/fontawesome-free-${FA_VERSION}-desktop.zip" -d vendor/upstream-fa/
rm -f "/tmp/fontawesome-free-${FA_VERSION}-desktop.zip"
echo "  -> vendor/upstream-fa/"

echo "Downloading Octicons ${OCTICONS_VERSION} from npm..."
curl -fsSL \
  "https://registry.npmjs.org/@primer/octicons/-/octicons-${OCTICONS_VERSION}.tgz" \
  | tar xz -C vendor/upstream-octicons/
echo "  -> vendor/upstream-octicons/"

echo "Writing sources manifest..."
cp sources.lock.json vendor/sources.json
echo "  -> vendor/sources.json"

echo "Done."
