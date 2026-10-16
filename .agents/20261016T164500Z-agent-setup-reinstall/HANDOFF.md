# Handoff

## Claim

The local checkout is installed at `/home/sparrow/.config/omarchy/plugins/sparesparrow.agent-setup`, with ID `sparesparrow.agent-setup`, version `1.0.0`. The Omarchy shell discovered it as enabled. All 67 deployable files match the tested checkout by SHA-256 and mode. The existing test script now validates the current Omarchy panel API and passes.

## Proof (exact commands, output or artifacts)

- `omarchy-plugin-validate .` — exit 0.
- Baseline `timeout 30s ./test.sh` — exit 1 because it asserted obsolete `qs.components` (and subsequent obsolete `JsonAdapter`/`Process`/`Translations.tr` contracts).
- `timeout 60s ./test.sh` after repair — exit 0, 37 tests pass; final output is `logs/test-sh-final.log`.
- `python3 -m unittest discover -s tests -p 'test_*.py'` — exit 0, 37 tests.
- `python3 -m unittest discover -s research -p 'test_*.py'` — exit 0, 32 tests.
- `python3 -m unittest discover -s router -p 'test_*.py'` — exit 0, 15 tests.
- `bash -n browser/setup-playwright-mcp.sh workspace/research-workspace.sh test.sh` — exit 0.
- `PYTHONPYCACHEPREFIX=/tmp/agent-setup-final-pycache python3 -m py_compile research/*.py research/synthesis/*.py orchestration/*.py router/*.py` — exit 0.
- `git diff --check` — exit 0.
- `omarchy restart shell` — exit 0 after approved external-sandbox execution; `omarchy-shell shell ping` returned `ok`.
- `omarchy-shell shell listPlugins` — plugin reports `enabled: true`.
- `omarchy-shell shell summon sparesparrow.agent-setup '{}'` returned `ok`; `omarchy-shell shell hide sparesparrow.agent-setup` returned `ok`.
- Local `rsync -a --delete --exclude=.git/ --exclude=.agents/ ./ ~/.config/omarchy/plugins/sparesparrow.agent-setup/`; repeat `rsync -ai ...` made zero changes. Installed validation passed and the 67 file/mode/hash records match in `DEPLOYABLE-MANIFEST.txt`.
- Action tests confirm the five declarative action arrays, their local targets, absence of shell-command interpolation, and a mocked argv path containing spaces. This mock is not live QML execution.

## Not proven

- Panel visual layout, actual clickable regions, Escape/outside-click/inside-click interactions, live English/Czech switching, and visible labels were not observed.
- The desktop Markdown handler did not open the Prompt Catalog guide during this run; the action path is verified statically and via mocked argv only.
- Perplexity/Gemini launches, workspace placement, and persisted profile behavior were not run.
- The Plan action did not start an agent. No prompt was sent and no provider was contacted.
- Browser MCP setup and real browser integration were not run. Setup would change Codex MCP configuration and invoke `npx`.
- Provider account billing settings cannot be proven by local source inspection. No paid-service activity was performed.
- Independent evaluator review: NOT PERFORMED.

## Safety boundary

No agent, provider, browser automation, network dispatch, credential access, MCP registration, GitHub write, push, merge, or package installation was performed. Test state was isolated. The only shell configuration backup was read-only and no intended config edit was made. Pre-existing file mode changes were preserved. The only implementation changes are tests/validation in `test.sh` and `tests/test_prompt_catalog_panel.py`.

## Rollback

See `ARTIFACT-INDEX.md`. Restore the previous installed directory from `backups/installed-plugin.before` with `cp -a`; optionally restore `backups/shell.json.before` if reverting the captured shell config is desired; then use `omarchy restart shell`. The source checkout was not reset or overwritten.

## Next owner: EVALUATOR | ORCHESTRATOR | USER

Independent review was not available/performed. The user can review the scoped test diff and decide whether to schedule direct visual/interaction checks at a desktop session.
