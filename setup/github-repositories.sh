#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_terminal "$@"
say "GitHub repozitare a skills pro tym agentu"
say "Vychozi klony: ~/Projects; jine adresare lze zadat. Existujici klony se neaktualizuji ani neprepisuji."
read -r -p "Adresar pro nove klony [${HOME}/Projects]: " root
root=${root:-"$HOME/Projects"}
read -r -p "Dalsi adresar pro hledani existujicich klonu (prazdny = zadny): " search
args=(--root "$root")
[[ -z "$search" ]] || args+=(--search-root "$search")
if confirm "Otevrit pruvodce SSH klicem a registraci verejneho klice na GitHub?"; then
  python3 "$(dirname "$0")/github-repositories.py" --ssh-setup
fi
python3 "$(dirname "$0")/github-repositories.py" "${args[@]}"
if confirm "Provest plan? Kazde klonovani i instalaci skills potvrdis zvlast"; then
  python3 "$(dirname "$0")/github-repositories.py" "${args[@]}" --apply
fi
if confirm "Pripravit nativni nacitani skills pro omp, OpenCode a OpenClaw (globalni i projektove)?"; then
  clients=(omp opencode openclaw)
  read -r -p "Grok varianta [none/build/community; vychozi none]: " grok
  case "${grok:-none}" in
    build) clients+=(grok-build) ;;
    community) clients+=(grok-cli) ;;
    none) ;;
    *) say "Neznama varianta Groku, vynechavam ji." ;;
  esac
  python3 "$(dirname "$0")/client-skills.py" "${args[@]}" --clients "${clients[@]}" --scope both
  if confirm "Provest tento plan skills? Kazdy cil potvrdis zvlast"; then
    python3 "$(dirname "$0")/client-skills.py" "${args[@]}" --clients "${clients[@]}" --scope both --apply
  fi
fi
pause_at_end
