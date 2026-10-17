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
if confirm "Připravit nativní načítání skills pro omp, OpenCode a OpenClaw (globální i projektové)?"; then
  clients=(omp opencode openclaw)
  read -r -p "Grok varianta [none/build/community; výchozí none]: " grok
  case "${grok:-none}" in
    build) clients+=(grok-build) ;;
    community) clients+=(grok-cli) ;;
    none) ;;
    *) say "Neznámá varianta Groku, vynechávám ji." ;;
  esac
  python3 "$(dirname "$0")/client-skills.py" "${args[@]}" --clients "${clients[@]}" --scope both
  if confirm "Provést tento plán skills? Každý cíl potvrdíš zvlášť"; then
    python3 "$(dirname "$0")/client-skills.py" "${args[@]}" --clients "${clients[@]}" --scope both --apply
  fi
fi
pause_at_end
