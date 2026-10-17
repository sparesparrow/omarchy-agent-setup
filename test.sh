#!/bin/bash

# Validates the plugin manifest, localization catalogs, executable sources, and agent contracts.

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")"

omarchy-plugin-validate .

for script in browser/*.sh workspace/*.sh setup/*.sh; do
  bash -n "$script"
done

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/omarchy-agent-setup-pycache" python3 -m py_compile research/dispatcher.py orchestration/handoff_dispatcher.py orchestration/workflow_templates.py orchestration/prompt_catalog.py setup/mia-voice-console.py
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

python3 - <<'PY'
import json
import re
from pathlib import Path

panel = Path("Panel.qml").read_text(encoding="utf-8")
manifest = json.loads(Path("manifest.json").read_text(encoding="utf-8"))
if manifest.get("entryPoints", {}).get("panel") != "Panel.qml":
    raise SystemExit("manifest panel entry point must target Panel.qml")
if "import qs.Commons as Commons" not in panel:
    raise SystemExit("Panel.qml must use Omarchy's qs.Commons API")
if "import Quickshell.Io" not in panel or 'Qt.resolvedUrl("i18n/en.json")' not in panel or 'Qt.resolvedUrl("i18n/cs.json")' not in panel:
    raise SystemExit("Panel.qml must load both packaged localization catalogs with Quickshell.Io")
if "Quickshell.execDetached(command)" not in panel:
    raise SystemExit("Panel.qml must execute the structured argument array directly")
if re.search(r'execDetached\(\s*"|bash\s+-c|shellQuote', panel):
    raise SystemExit("Panel.qml must not turn action arguments into shell command text")
if "function open(payloadJson)" not in panel or "function close()" not in panel:
    raise SystemExit("Panel.qml must implement the shell panel open/close lifecycle")
if "PanelWindow {" not in panel or "WlrLayershell.layer: WlrLayer.Overlay" not in panel:
    raise SystemExit("Panel.qml must use Omarchy's supported overlay PanelWindow")
if "OverlayWindow {" in panel:
    raise SystemExit("Panel.qml must not use the unsupported OverlayWindow type")
if "Qt.Key_Escape" not in panel or "root.dismiss()" not in panel:
    raise SystemExit("Panel.qml must support Escape dismissal")
if 'root.language = "en"' not in panel or 'root.language = "cs"' not in panel:
    raise SystemExit("Panel.qml must support live English/Czech switching")
if "function activateFocused()" not in panel or "root.moveFocus(1)" not in panel:
    raise SystemExit("Panel.qml must make its language and action controls keyboard-operable")
if 'color: Qt.rgba(0.07, 0.07, 0.07, 0.98)' not in panel:
    raise SystemExit("Panel.qml must keep desktop content from bleeding through the action card")

expected_actions = {
    "action.research.title": ["workspace/research-workspace.sh"],
    "action.openclaw.title": ["setup/openclaw-cs.sh"],
    "action.voxtype.title": ["setup/voxtype.sh"],
    "action.plugins.title": ["setup/plugins.sh"],
    "action.ecosystem.title": ["setup/omarchy-ecosystem.sh"],
    "action.omp.title": ["setup/omp-presets.sh"],
    "action.mia.title": ["setup/mia-voice.sh"],
    "action.catalog.title": ["prompt-catalog/README.md"],
    "action.mcp.title": ["setup/mcp-skills.sh"],
    "action.team.title": ["setup/agent-team.sh"],
    "action.repositories.title": ["setup/github-repositories.sh"],
}
removed_actions = ("action.plan.title", "action.audit.title", "action.notes.title")

for expected, targets in expected_actions.items():
    if expected not in panel:
        raise SystemExit(f"panel is missing the action key {expected}")
    for target in targets:
        if not Path(target).is_file():
            raise SystemExit(f"panel action target is missing: {target}")
        if target not in panel:
            raise SystemExit(f"panel does not reference {target}")
for removed in removed_actions:
    if removed in panel:
        raise SystemExit(f"removed panel action is still present: {removed}")

actions = re.findall(r"\{\s*titleKey:.*?\n    \}", panel, re.DOTALL)
if len(actions) != len(expected_actions):
    raise SystemExit(f"expected {len(expected_actions)} panel actions, found {len(actions)}")
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
used = set(re.findall(r'root\.t\("([a-z0-9.]+)"\)', panel))
used.update(re.findall(r'(?:titleKey|detailKey): "([a-z0-9.]+)"', panel))
if used != source_keys:
    missing = sorted(source_keys - used)
    unknown = sorted(used - source_keys)
    raise SystemExit(f"Panel/catalog key mismatch: unreferenced={missing}, unknown={unknown}")

for key in source_keys:
    if panel.count(f'"{key}"') != 1:
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
