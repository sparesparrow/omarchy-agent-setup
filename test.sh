#!/bin/bash

# Validates the plugin manifest, localization catalogs, executable sources, and agent contracts.

set -euo pipefail
cd "$(dirname "$0")"

omarchy-plugin-validate .

for script in browser/*.sh workspace/*.sh; do
  bash -n "$script"
done

python3 -m py_compile research/dispatcher.py orchestration/handoff_dispatcher.py orchestration/workflow_templates.py orchestration/prompt_catalog.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 orchestration/prompt_catalog.py list >/dev/null

for required in \
  "## Claim" \
  "## Proof (exact commands, output or artifacts)" \
  "## Not proven" \
  "## Safety boundary" \
  "## Rollback" \
  "## Next owner: EVALUATOR | ORCHESTRATOR | USER"; do
  grep -Fq "$required" templates/HANDOFF.md || { echo "HANDOFF.md missing: $required" >&2; exit 1; }
done

for required in \
  "## Verdict: PASS | FAIL" \
  "## Acceptance checklist" \
  "## Unverified claims" \
  "## Next owner: EXECUTOR | ORCHESTRATOR | USER"; do
  grep -Fq "$required" templates/EVALUATION.md || { echo "EVALUATION.md missing: $required" >&2; exit 1; }
done

grep -Fq "Do not evaluate or approve your own work" prompts/executor-codex.md
grep -Fq "Do not edit implementation files" prompts/evaluator-grok.md
grep -Fq "Not proven" AGENTS.md

grep -Fq 'import qs.components' Panel.qml || { echo "Panel.qml must use the packaged Quickshell component import" >&2; exit 1; }
grep -Fq 'as Components' Panel.qml && { echo "Panel.qml must not use the legacy qs.components alias" >&2; exit 1; }

grep -Fq 'JsonAdapter' Panel.qml || { echo "Panel.qml must parse Process output with JsonAdapter" >&2; exit 1; }
grep -Fq 'JSON.parse' Panel.qml && { echo "Panel.qml must not call JSON.parse on Process output" >&2; exit 1; }

python3 - <<'PY'
from pathlib import Path

text = Path("Panel.qml").read_text(encoding="utf-8")
blocks = text.split("Process {")[1:]
if not blocks:
    raise SystemExit("Panel.qml has no Process objects")
for index, block in enumerate(blocks, 1):
    process = block.split("}", 1)[0]
    if "onExited" not in process:
        raise SystemExit(f"Process block {index} must handle onExited")
PY

python3 - <<'PY'
import json
import re
from pathlib import Path

catalog_dir = Path("i18n")
paths = sorted(catalog_dir.glob("*.json"))
if not paths:
    raise SystemExit("No localization catalogs found")

catalogs = {}
for path in paths:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    catalogs[path.name] = data

source = catalogs.get("en.json")
if source is None:
    raise SystemExit("i18n/en.json is required as the source catalog")
source_keys = set(source)
if not source_keys:
    raise SystemExit("i18n/en.json is empty")

for name, data in catalogs.items():
    if set(data) != source_keys:
        missing = sorted(source_keys - set(data))
        extra = sorted(set(data) - source_keys)
        raise SystemExit(f"{name} key mismatch: missing={missing}, extra={extra}")
    for key, value in data.items():
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"{name}:{key} must be a non-empty string")

panel = Path("Panel.qml").read_text(encoding="utf-8")
used = set(re.findall(r'Translations\.tr\("([a-z0-9.]+)"\)', panel))
if used != source_keys:
    missing = sorted(source_keys - used)
    unknown = sorted(used - source_keys)
    raise SystemExit(f"Panel/catalog key mismatch: unreferenced={missing}, unknown={unknown}")

for key in source_keys:
    if panel.count(f'Translations.tr("{key}")') != 1:
        raise SystemExit(f"Panel must reference {key} exactly once")

for forbidden in (
    "Agent Setup",
    "Research workspace",
    "Plan with agents",
    "Payment audit",
    "Dispatcher notes",
):
    if forbidden in panel:
        raise SystemExit(f"Hardcoded visible label remains in Panel.qml: {forbidden}")

text_items = re.findall(r"Text\s*\{(.*?)\n\s*\}", panel, re.DOTALL)
if len(text_items) < 2:
    raise SystemExit("Expected title and card Text items")
for block in text_items:
    if "textFormat: Text.PlainText" not in block:
        raise SystemExit("Every plugin Text item must force Text.PlainText")
PY
