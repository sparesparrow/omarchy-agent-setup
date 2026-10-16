# Checkpoints

Run started 2026-10-16 18:41 CEST, ended 2026-10-16 18:47 CEST. Checkout remained at `cf681a1e022fce4f7ac3686bdd616ab290768646`, branch `main`. Initial changes were mode-only on `browser/setup-playwright-mcp.sh`, `test.sh`, and `workspace/research-workspace.sh`; the run added test content changes to `test.sh` and `tests/test_prompt_catalog_panel.py`. No source/runtime `Panel.qml`, scripts, catalog, or config was changed.

| Checkpoint | Time | Commands / result | Expected vs observed | Evidence | Status / evidence type |
|---|---|---|---|---|---|
| 0 Discovery/baseline | 18:41–18:42 | `git status --short --branch`, `git rev-parse HEAD`, `omarchy plugin --help/list`, `omarchy-plugin-validate .`; inspected Omarchy shell/plugin source and runtime | Existing local checkout and one installed copy; discovered enabled state initially unavailable while shell stopped; confirmed plugin path under `~/.config/omarchy/plugins` | `backups/installed-plugin.before`, `backups/shell.json.before`; initial shell state said stopped; `manifest.json` | PASS, static/integration |
| 1 Baseline tests | 18:42 | `timeout 30s ./test.sh` (1); `omarchy-plugin-validate .` (0); `python3 -m unittest discover -s tests -p 'test_*.py'` (36 pass) | Manifest and Python tests pass; test script fails on stale `qs.components` requirement | Baseline tool output recorded in conversation; final logs preserve post-fix commands | PASS with expected test failure diagnosed, automated |
| 2 Repairs | 18:43–18:46 | Edited only `test.sh` and `tests/test_prompt_catalog_panel.py`; repeated tests | Old requirements for `JsonAdapter`, `Process/onExited`, and `Translations.tr` replaced with checks for current Omarchy API, panel lifecycle, declarative action keys, target files, structured argv, and locale keys. Added path-with-spaces mock. | Final diff; `logs/test-sh-final.log` | PASS, automated/static |
| 3 Local reinstall | 18:43–18:47 | Local `rsync -a --delete --exclude=.git/ --exclude=.agents/ ./ ~/.config/omarchy/plugins/sparesparrow.agent-setup/`; `omarchy-plugin-validate` | Exact local build installed; no remote source used. Repeat rsync changed 0 entries. 67/67 deployable files match SHA-256 and mode. | `DEPLOYABLE-MANIFEST.txt`, `logs/reinstall-repeat.log` | PASS, integration/static |
| 4 Panel/localization | 18:44–18:46 | Approved `timeout 30s omarchy restart shell`; `omarchy-shell shell ping`; `listPlugins`; `shell summon ... '{}'`; `shell hide ...` | Shell restarted and answered; plugin enabled; summon/hide return `ok`. Direct IPC was required outside sandbox. No visual, keyboard, outside-click, card-layout, language-switch observation. | Narrow plugin list and IPC output in run record; targeted journal query had no matching QML error/warning | PARTIAL, integration; visual NOT RUN |
| 5 Prompt catalog/templates | 18:42–18:47 | `python3 orchestration/prompt_catalog.py --help`; `python3 orchestration/workflow_templates.py --help`; automated test suites | CLI syntax inspected; catalog and template negative/positive fixture coverage passed in their test suites. No source catalog mutation. | `logs/tests-suite.log`; source tests | PASS, automated/mocked |
| 6 Dispatch/router/workspace/browser/audit | 18:42–18:47 | Individual research/router/repo suites; `bash -n ...`; Python compilation; source audit | Dispatcher/input guard/synthesis/router/handoff contract fixtures pass. Workspace launches and agent/browser actions were not run. Browser script not run because it registers MCP and invokes `npx`; no setup config changed. | `logs/research-suite.log`, `logs/router-suite.log`; static source audit | PARTIAL by feature, automated/static/mocked |
| 7 Repeatability/cleanup | 18:46–18:47 | Repeated local rsync; `git diff --check`; installed validation; generated cache cleanup | Idempotent install, no active duplicate, test-created `__pycache__` removed; shell stayed enabled from pre-existing state. | `DEPLOYABLE-MANIFEST.txt`, `logs/reinstall-repeat.log` | PASS, integration/static |
| 8 Handoff | 18:47 | Report and matrix written | Evidence distinguishes mock from live; evaluator not invoked | `HANDOFF.md`, `FEATURE-MATRIX.md`, `ARTIFACT-INDEX.md` | PASS, documentation |

## Final automated totals

- `./test.sh`: 37 passed.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: 37 passed.
- `python3 -m unittest discover -s research -p 'test_*.py'`: 32 passed.
- `python3 -m unittest discover -s router -p 'test_*.py'`: 15 passed.
- Total distinct discovered tests: 84; all pass.
- `bash -n browser/setup-playwright-mcp.sh workspace/research-workspace.sh test.sh`: exit 0.
- Python compile of `research/*.py research/synthesis/*.py orchestration/*.py router/*.py` with external pycache: exit 0.
- Source and installed manifest validation: exit 0. `git diff --check`: exit 0.

No live web-app, provider, browser MCP, real agent, QML visual interaction, or evaluator activity occurred.
