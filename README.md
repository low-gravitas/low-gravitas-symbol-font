# Low Gravitas Symbols

A symbol-only font that extends Nerd Fonts v3.4.0 with newer glyphs from Codicons, Font Awesome, and Octicons.

## Why?

Nerd Fonts v3.4.0 bundles stale versions of its glyph sources:
- **Codicons**: missing ~100 newer glyphs (U+EC1F–EC84) including Claude (U+EC82), OpenAI, MCP, and Agent icons
- **Font Awesome**: stuck at 6.5.1 (latest LTS is 6.7.2)
- **Octicons**: stuck at 18.3.0 (latest is 19.22.0)

This font fills those gaps. Use it as a fallback font alongside your Nerd Font of choice.

## Prerequisites

```bash
brew install fontforge jq
```

## Build

```bash
make update   # Download font-patcher + upstream font sources
make build    # Build LowGravitasSymbols.ttf
make install  # Copy to ~/Library/Fonts/
```

## Ghostty Configuration

```
font-family = "JetBrainsMono Nerd Font Mono"
font-family = "Low Gravitas Symbols"
```

## Verify

```bash
printf '\uE0B0'   # Powerline arrow
printf '\uF31B'   # Ubuntu logo
printf '\uEC82'   # Claude icon
```

## Codepoint Ranges

| Glyph Set | Range | Source |
|-----------|-------|--------|
| Pomicons | U+E000–E00A | font-patcher |
| Powerline | U+E0A0–E0A2, E0B0–E0B3 | font-patcher |
| Powerline Extra | U+E0A3, E0B4–E0C8, E0CA, E0CC–E0D7 | font-patcher |
| Font Awesome Ext | U+E200–E2A9 | font-patcher |
| Weather Icons | U+E300–E3E3 | font-patcher |
| Seti-UI + Custom | U+E5FA–E6B7 | font-patcher |
| Devicons | U+E700–E8EF | font-patcher |
| Codicons (base) | U+EA60–EC1E | font-patcher |
| **Codicons (new)** | **U+EC1F–EC84** | **merge script** |
| Font Awesome (base) | U+ED00–F2FF | font-patcher |
| **Font Awesome (new)** | **U+F2FF+** | **merge script** |
| Font Logos | U+F300–F381 | font-patcher |
| Octicons (base) | U+F400–F533 | font-patcher |
| **Octicons (new)** | **U+F533+** | **merge script** |
| Material Design | U+F500–FD46, F0001–F1AF0 | font-patcher |

## License

The generated font contains glyphs from multiple sources, each under their own license:
- [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) — MIT
- [Codicons](https://github.com/microsoft/vscode-codicons) — CC-BY-4.0
- [Font Awesome Free](https://github.com/FortAwesome/Font-Awesome) — CC-BY-4.0 / SIL OFL 1.1
- [Octicons](https://github.com/primer/octicons) — MIT
