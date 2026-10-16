# Artifact index and rollback

## Evidence

- `PLAN.md`, `TASKS.md`, `ACCEPTANCE.md`: task scope and execution.
- `CHECKPOINTS.md`: timestamps, commands, outcomes, test counts, and evidence type.
- `FEATURE-MATRIX.md`: separate static, automated, mocked, and live columns.
- `HANDOFF.md`: executor claim, proof, limitations, safety, rollback, and next owner.
- `logs/test-sh-final.log`: final `./test.sh` output (37 passing).
- `logs/tests-suite.log`: repository suite (37 passing).
- `logs/research-suite.log`: research suite (32 passing).
- `logs/router-suite.log`: router suite (15 passing).
- `logs/reinstall-repeat.log`: repeat sync; zero changed entries.
- `DEPLOYABLE-MANIFEST.txt`: installed/check-out relative paths, modes, and SHA-256 values; `.git`, `.agents`, and Python cache artifacts excluded.
- `backups/installed-plugin.before`: `cp -a` backup of the previous installed plugin, including permissions and `.git` metadata.
- `backups/shell.json.before`: `cp -a` backup of the shell config before the enable/reload checkpoint. The plugin was already enabled, so this run made no intentional shell configuration change.

## Rollback

The current candidate is the local checkout at `/home/sparrow/omarchy-agent-setup`, installed under `/home/sparrow/.config/omarchy/plugins/sparesparrow.agent-setup`.

To restore the prior installed plugin copy, first preserve the current candidate if desired, then replace the installed directory with `backups/installed-plugin.before` using `cp -a`. Restore `backups/shell.json.before` to `/home/sparrow/.config/omarchy/shell.json` only if you specifically want to revert shell configuration to its captured pre-run state. Then run `omarchy restart shell` and verify `omarchy-shell shell ping`. No other configuration backup is involved.

Only test-generated `__pycache__` directories were removed; source changes and the evidence/backup directory remain available.
