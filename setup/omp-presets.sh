#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_terminal "$@"
ROOT=$(setup_root)
say "Oh My Pi — předvolby rolí. Neurčují placený model."
if ! command -v omp >/dev/null 2>&1; then
  say "Pro instalaci napiš přesně: NAINSTALOVAT OMP"
  read -r -p "> " phrase
  if [[ "$phrase" == "NAINSTALOVAT OMP" ]]; then
    curl -fsSL https://omp.sh/install | sh
  else
    say "Instalaci omp jsem nespustil."
  fi
fi
dest="${HOME}/.omp/agent/presets"
mkdir -p "$dest"
for preset in mia libertin human-action omarchy-steward software; do
  if confirm "Zkopírovat ${preset} do ${dest}?"; then
    target="${dest}/${preset}.md"
    if [[ -e "$target" ]]; then
      say "${target} už existuje, přeskakuji."
    else
      cp "$ROOT/omp-presets/${preset}.md" "$target"
    fi
  fi
done
if confirm "Zapsat předvolbu do checkoutu jako .omp/AGENTS.md?"; then
  read -r -p "Cesta k repozitáři: " repo
  read -r -p "Předvolba: " preset
  if [[ -d "$repo" && -f "$ROOT/omp-presets/${preset}.md" && ! -e "$repo/.omp/AGENTS.md" ]]; then
    mkdir -p "$repo/.omp"
    cp "$ROOT/omp-presets/${preset}.md" "$repo/.omp/AGENTS.md"
  else
    say "Cesta není platná, nebo soubor už existuje. Nic jsem nepřepsal."
  fi
fi
pause_at_end
