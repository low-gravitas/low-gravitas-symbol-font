#!/bin/bash
set -euo pipefail

# Downloads font-patcher and glyph source fonts from nerd-fonts v3.4.0
# Preserves the directory structure font-patcher expects (resolves paths relative to its own location)

NF_VERSION="v3.4.0"
BASE_URL="https://raw.githubusercontent.com/ryanoasis/nerd-fonts/${NF_VERSION}"

mkdir -p vendor/src/glyphs/codicons \
         vendor/src/glyphs/devicons \
         vendor/src/glyphs/font-awesome \
         vendor/src/glyphs/materialdesign \
         vendor/src/glyphs/octicons \
         vendor/src/glyphs/pomicons \
         vendor/src/glyphs/powerline-extra \
         vendor/src/glyphs/powerline-symbols \
         vendor/src/glyphs/weather-icons \
         vendor/bin/scripts/name_parser

echo "Downloading font-patcher..."
curl -fsSL "${BASE_URL}/font-patcher" -o vendor/font-patcher
chmod +x vendor/font-patcher

echo "Downloading glyph source fonts..."

# Core glyph sources (at root of src/glyphs/)
curl -fsSL "${BASE_URL}/src/glyphs/original-source.otf" -o vendor/src/glyphs/original-source.otf
curl -fsSL "${BASE_URL}/src/glyphs/extraglyphs.sfd" -o vendor/src/glyphs/extraglyphs.sfd
curl -fsSL "${BASE_URL}/src/glyphs/font-awesome-extension.ttf" -o vendor/src/glyphs/font-awesome-extension.ttf
curl -fsSL "${BASE_URL}/src/glyphs/font-logos.ttf" -o vendor/src/glyphs/font-logos.ttf

# Subdirectory glyph sources (font-patcher resolves these relative to src/glyphs/)
curl -fsSL "${BASE_URL}/src/glyphs/codicons/codicon.ttf" -o vendor/src/glyphs/codicons/codicon.ttf
curl -fsSL "${BASE_URL}/src/glyphs/devicons/devicons.otf" -o vendor/src/glyphs/devicons/devicons.otf
curl -fsSL "${BASE_URL}/src/glyphs/font-awesome/FontAwesome.otf" -o vendor/src/glyphs/font-awesome/FontAwesome.otf
curl -fsSL "${BASE_URL}/src/glyphs/materialdesign/MaterialDesignIconsDesktop.ttf" -o vendor/src/glyphs/materialdesign/MaterialDesignIconsDesktop.ttf
curl -fsSL "${BASE_URL}/src/glyphs/octicons/octicons.otf" -o vendor/src/glyphs/octicons/octicons.otf
curl -fsSL "${BASE_URL}/src/glyphs/pomicons/Pomicons.otf" -o vendor/src/glyphs/pomicons/Pomicons.otf
curl -fsSL "${BASE_URL}/src/glyphs/powerline-extra/PowerlineExtraSymbols.otf" -o vendor/src/glyphs/powerline-extra/PowerlineExtraSymbols.otf
curl -fsSL "${BASE_URL}/src/glyphs/powerline-symbols/PowerlineSymbols.otf" -o vendor/src/glyphs/powerline-symbols/PowerlineSymbols.otf
curl -fsSL "${BASE_URL}/src/glyphs/weather-icons/weathericons-regular-webfont.ttf" -o vendor/src/glyphs/weather-icons/weathericons-regular-webfont.ttf

echo "Downloading font-patcher helper scripts and data..."
curl -fsSL "${BASE_URL}/bin/scripts/name_parser/FontnameParser.py" -o vendor/bin/scripts/name_parser/FontnameParser.py
curl -fsSL "${BASE_URL}/bin/scripts/name_parser/FontnameTools.py" -o vendor/bin/scripts/name_parser/FontnameTools.py
curl -fsSL "${BASE_URL}/glyphnames.json" -o vendor/glyphnames.json

echo "Done. All font-patcher dependencies downloaded to vendor/"
