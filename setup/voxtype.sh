#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_terminal "$@"
say "Voxtype — diktování na Omarchy"
say "Po instalaci držíš F9 nebo přepínáš Super+Ctrl+X. Výchozí model je anglický."
if ! command -v voxtype >/dev/null 2>&1; then
  if command -v omarchy >/dev/null 2>&1 && confirm "Nainstalovat: omarchy pkg add voxtype-bin?"; then
    omarchy pkg add voxtype-bin
  else
    say "Voxtype jsem nenainstaloval. V menu je také Install > AI > Dictation."
    pause_at_end
    exit 1
  fi
fi
if command -v voxtype >/dev/null 2>&1 && confirm "Spustit výběr modelu: voxtype setup model?"; then
  voxtype setup model
fi
pause_at_end
