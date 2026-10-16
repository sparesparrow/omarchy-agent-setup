# Acceptance

- Installed ID/version remains `sparesparrow.agent-setup` / `1.0.0` and its deployable file hashes and permissions match this local checkout.
- Manifest validation passes; plugin is discovered, enabled, summonable, and hideable using supported Omarchy IPC.
- `test.sh`, all repository/research/router tests, shell syntax checks, Python compilation, and `git diff --check` pass.
- Test validation follows actual `qs.Commons`, `Commons.Translations`, key-based `strings.t()`, lifecycle hooks, and structured `Quickshell.execDetached(argv)` behavior.
- All five actions and localized text keys/targets are covered; an isolated mock checks argv preservation when a local path contains spaces.
- Feature evidence keeps static, automated, mocked, and live desktop results separate. UI details not directly observed remain NOT RUN.
- Existing local edits remain; no providers, APIs, browser MCP, credentials, or GitHub writes are used.
