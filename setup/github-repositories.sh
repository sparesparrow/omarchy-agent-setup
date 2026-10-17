#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_terminal "$@"
say "GitHub repozitáře a skills pro tým agentů"
say "Výchozí klony: ~/Projects; jiné adresáře lze zadat. Existující klony se neaktualizují ani nepřepisují."
read -r -p "Adresář pro nové klony [${HOME}/Projects]: " root
root=${root:-"$HOME/Projects"}
read -r -p "Další adresář pro hledání existujících klonů (prázdný = žádný): " search
args=(--root "$root")
[[ -z "$search" ]] || args+=(--search-root "$search")
if confirm "Otevřít průvodce SSH klíčem a registrací veřejného klíče na GitHub?"; then
  python3 "$(dirname "$0")/github-repositories.py" --ssh-setup
fi
python3 "$(dirname "$0")/github-repositories.py" "${args[@]}"
if confirm "Provést plán? Každé klonování i instalaci skills potvrdíš zvlášť"; then
  python3 "$(dirname "$0")/github-repositories.py" "${args[@]}" --apply
fi
pause_at_end
