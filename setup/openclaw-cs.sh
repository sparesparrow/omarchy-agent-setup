#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_terminal "$@"
ROOT=$(setup_root)
say "OpenClaw — interaktivní nastavení koordinátora v češtině"
say "Tento krok nic sám neodesílá, nespouští agenta a nemění fakturaci."
if ! command -v openclaw >/dev/null 2>&1; then
  say "Příkaz openclaw není nainstalovaný."
  if command -v omarchy >/dev/null 2>&1 && confirm "Zkusit: omarchy install openclaw?"; then
    omarchy install openclaw
  else
    say "Instalaci jsem nespustil."
    pause_at_end
    exit 1
  fi
fi
if ! command -v openclaw >/dev/null 2>&1; then
  say "OpenClaw po instalaci stále není v PATH."
  pause_at_end
  exit 1
fi
if confirm "Spustit openclaw setup --wizard?"; then
  openclaw setup --wizard || openclaw setup
fi
target="${HOME}/.openclaw/workspace/ORCHESTRATOR.cs.md"
if confirm "Uložit český kontrakt do ${target}? Existující soubor se nepřepíše."; then
  mkdir -p "$(dirname "$target")"
  if [[ -e "$target" ]]; then
    say "Soubor už existuje, nechávám ho."
  else
    cp "$ROOT/prompts/orchestrator-openclaw-cs.md" "$target"
    say "Uloženo. openclaw.json jsem neměnil."
  fi
fi
pause_at_end
