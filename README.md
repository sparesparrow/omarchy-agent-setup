# Omarchy Agent Setup

A reviewed Omarchy plugin plus the local agent workflow used to build it. It brings the research workspace, browser automation, research dispatcher, agent handoffs, quota fallback, and payment audit from this repository into one installable package.

## Install

```bash
omarchy-plugin-install https://github.com/sparesparrow/omarchy-agent-setup
```

Omarchy installs it as `omarchy-agent-setup`. If you already installed an older checkout under another name, remove that copy before installing this one.

After installation, reload the shell (`Super + Ctrl + R`), open **Install > Plugin**, enable **Agent Setup**, then add the panel to your bar.

Plugins run as unsandboxed code inside the Omarchy shell and land disabled so you can review them first. Read `Panel.qml`, `workspace/`, `browser/`, and `research/` before enabling or running their commands.

## What is included

- `Panel.qml` and `manifest.json` - the plugin: a card with four actions (research workspace, plan with agents, payment audit, dispatcher notes).
- `i18n/` - plugin-owned English and Czech catalogs that follow Omarchy's selected language live.
- `AGENTS.md`, `prompts/`, `templates/` - the orchestrator, executor, and evaluator contracts, role prompts, and handoff templates.
  Their role separation and evidence handoff selectively adapt the portable agent pattern from `sparesparrow/mia`; see `docs/mia-agent-patterns.md`.
- `prompt-catalog/` - a local, versioned, searchable prompt catalog with strict variable rendering, adapted from `sparesparrow/mcp-prompts` without a server, database, cloud account, or payment tier.
- `workspace/` - a Hyprland research workspace with Perplexity and Gemini as separate web apps.
- `browser/` - Playwright MCP setup for Codex, with a safety note.
- `research/` - a dispatcher that turns a `dispatch.yaml` into research jobs.
- `orchestration/` and `project-templates/` - dependency-free discovery and rendering of repo-aware Python, embedded, and Hyprland workflow contracts, adapted from `sparesparrow/mcp-project-orchestrator`.
- `docs/no-extra-payment-audit.md` - a checklist to make sure no agent can bill you.

## Localization

The panel loads `i18n/en.json` and `i18n/cs.json` through Omarchy's `Commons.Translations`. Omarchy selects the matching language, falls back to English, and updates text bindings while the panel is open.

Add new visible plugin text to both catalogs and reference it with `Translations.tr("key")`. Do not translate command IDs, process arguments, paths, service names, provider names, or handoff filenames. Keep every rendered plugin text item on `Text.PlainText`; translated strings must never become rich text.

The technical agent contracts remain canonical rather than being copied into 50 language trees. Add localized operator help only when there is a real reviewed translation workflow for it.

## Test

From a checkout on an Omarchy machine:

```bash
./test.sh
```

This validates the manifest, parses the scripts, compiles the Python tools, runs the workflow-template and prompt-catalog unit tests, checks English/Czech catalog parity, checks that every localization key is referenced, rejects previous hardcoded panel labels, and requires plain-text rendering for plugin text.

The panel still needs a running Omarchy shell for live verification. Test both English and Czech, switch between them while the panel is open, and verify that longer Czech labels wrap correctly.

## What is not automatic

This repository does not install Codex, Gemini, Grok, or Claude CLIs, log you into services, enable browser MCP, or run agents during plugin installation. Those actions may create security or quota risk and remain explicit user choices.

Run `browser/setup.sh` only after reviewing the Playwright MCP warning. Copy workspace files from `workspace/` only after backing up existing Hyprland configuration.
