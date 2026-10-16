#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_terminal "$@"
ROOT=$(setup_root)
say "MIA — hlasová konzole"
say "Konzole posílá jen tlačítka: probudit, hned, zrušit, ano, ne, konec diktátu a upovídanost."
say "POZOR: /ws/voice na Pi zatím ovládá simulovaný stroj uvnitř API, ne běžící hlasový router. Nic v autě to neovládá."
say "Kód kodeku se načítá z tvého checkoutu sparesparrow/mia. Zadej jen checkout, který jsi sám zkontroloval."
repo="${MIA_REPO:-$HOME/mia}"
read -r -p "Cesta k checkoutu MIA [${repo}]: " answer
repo="${answer:-$repo}"
if [[ ! -f "$repo/apps/rpi-backend/py-api/services/voice_fsm/wire/codec.py" ]]; then
  say "V ${repo} jsem nenašel hlasový kodek MIA. Nic jsem nespustil."
  pause_at_end
  exit 1
fi
url="${MIA_VOICE_URL:-}"
read -r -p "Adresa konzole, například ws://mia.local:8000/ws/voice [${url}]: " answer
url="${answer:-$url}"
if [[ -z "$url" ]]; then
  say "Adresa chybí."
  pause_at_end
  exit 1
fi
if [[ "$url" == ws://* ]]; then
  say "Nešifrované ws:// povolím jen pro lokální, soukromou nebo Tailscale adresu."
fi
key_env="MIA_API_KEY"
read -r -p "Název proměnné s API klíčem [${key_env}]: " answer
key_env="${answer:-$key_env}"
if [[ ! "$key_env" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  say "Neplatný název proměnné. Zadej název, ne samotný klíč."
  pause_at_end
  exit 1
fi
if [[ -z "${!key_env:-}" ]]; then
  say "Proměnná ${key_env} není nastavená. Klíč můžeš zadat jen pro tuto relaci (nezobrazí se, neuloží se)."
  if confirm "Zadat klíč teď?"; then
    read -r -s -p "API klíč: " typed
    echo
    export "${key_env}=${typed}"
  fi
fi
python3 "$ROOT/setup/mia-voice-console.py" --repo "$repo" --url "$url" --key-env "$key_env" || true
pause_at_end
