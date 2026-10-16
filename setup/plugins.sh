#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_terminal "$@"
say "Katalog pluginů Omarchy. Nic se nenainstaluje bez samostatného ano."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
downloaded=0
for url in https://omarchyplugins.com/catalog.json https://plugins.omarchy.org/catalog.json; do
  if curl -fsSL --max-time 20 "$url" -o "$tmp"; then
    downloaded=1
    break
  fi
done
if [[ "$downloaded" -eq 1 ]]; then
  python3 - "$tmp" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
items = data.get("plugins", data) if isinstance(data, dict) else data
if not isinstance(items, list):
    raise SystemExit("Katalog nemá seznam pluginů.")
shown = 0
for item in items:
    if not isinstance(item, dict):
        continue
    repo = item.get("repo") or item.get("repository") or item.get("git") or item.get("url") or ""
    if not repo:
        continue
    shown += 1
    print(f"{shown}\t{item.get('id','')}\t{item.get('name') or item.get('title') or item.get('id') or 'plugin'}\t{repo}")
    if shown == 40:
        break
if shown == 0:
    raise SystemExit("Katalog neobsahuje použitelné URL.")
PY
else
  say "Katalog se nepodařilo stáhnout. Můžeš vložit jednu https:// git URL."
fi
read -r -p "Čísla nebo jedna git URL: " selection
[[ -n "${selection}" ]] || { pause_at_end; exit 0; }
if [[ "$selection" == https://* ]]; then
  mapfile -t chosen < <(printf '%s\n' "$selection")
elif [[ "$downloaded" -ne 1 ]]; then
  say "Bez katalogu lze zadat jen URL."
  pause_at_end
  exit 1
else
  mapfile -t chosen < <(python3 - "$tmp" "$selection" <<'PY'
import json, sys
from pathlib import Path
wanted = {int(part) for part in sys.argv[2].split() if part.isdigit()}
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
items = data.get("plugins", data) if isinstance(data, dict) else data
shown = 0
for item in items:
    if not isinstance(item, dict):
        continue
    repo = item.get("repo") or item.get("repository") or item.get("git") or item.get("url") or ""
    if not repo:
        continue
    shown += 1
    if shown in wanted:
        print(repo)
PY
)
fi
for url in "${chosen[@]}"; do
  say "Zdroj: $url"
  if confirm "Nainstalovat bez zapnutí?"; then
    omarchy plugin add "$url"
    if confirm "Zapnout až po kontrole kódu?"; then
      read -r -p "Plugin id: " plugin_id
      [[ -n "$plugin_id" ]] && omarchy plugin enable "$plugin_id"
    fi
  fi
done
pause_at_end
