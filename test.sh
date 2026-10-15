#!/bin/bash

# Validates the plugin manifest, localization catalogs, and executable sources.

set -euo pipefail
cd "$(dirname "$0")"

omarchy-plugin-validate .

for script in browser/*.sh workspace/*.sh; do
  bash -n "$script"
done

python3 -m py_compile research/dispatcher.py

python3 - <<'PY'
import json
import re
from pathlib import Path

panel = Path("Panel.qml").read_text()
english = json.loads(Path("i18n/en.json").read_text())
czech = json.loads(Path("i18n/cs.json").read_text())

if set(czech) != set(english):
    missing = sorted(set(english) - set(czech))
    extra = sorted(set(czech) - set(english))
    raise SystemExit(f"Czech catalog differs from English; missing={missing}, extra={extra}")

for code, catalog in (("en", english), ("cs", czech)):
    empty = sorted(key for key, value in catalog.items() if not isinstance(value, str) or not value.strip())
    if empty:
        raise SystemExit(f"{code} catalog has invalid values: {empty}")

literal_keys = set(re.findall(r'strings\.t\("([a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)+)"\)', panel))
dynamic_keys = set(re.findall(r'(?:titleKey|detailKey):\s*"([a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)+)"', panel))
referenced = literal_keys | dynamic_keys

missing = sorted(referenced - set(english))
unreferenced = sorted(set(english) - referenced)
if missing or unreferenced:
    raise SystemExit(f"catalog references differ; missing={missing}, unreferenced={unreferenced}")

for old_text in ("AGENT SETUP", "Research workspace", "Plan with agents", "No-extra-payment audit", "Research dispatcher notes"):
    if old_text in panel:
        raise SystemExit(f"hardcoded display text remains in Panel.qml: {old_text}")

if panel.count("textFormat: Text.PlainText") < 3:
    raise SystemExit("every plugin Text element must explicitly use Text.PlainText")
PY

echo "ok"
