# Agent setup (Omarchy plugin)

An [Omarchy](https://omarchy.org) shell plugin and a set of working files for running several coding agents together: Claude orchestrates, Codex executes, Grok evaluates, and Gemini is the fallback, with a browser research workspace.

## Install

```bash
omarchy plugin add https://github.com/sparesparrow/omarchy-agent-setup.git
omarchy plugin enable sparesparrow.agent-setup
omarchy-shell shell summon sparesparrow.agent-setup '{}'
```

Plugins run as unsandboxed code inside the Omarchy shell and land disabled so you can read them first. This one only launches the commands listed below when you click a button.

## What is in it

- `Panel.qml` and `manifest.json` - the plugin: a card with four actions (research workspace, plan with agents, payment audit, dispatcher notes).
- `i18n/` - plugin-owned English and Czech catalogs that follow Omarchy's selected language live.
- `AGENTS.md`, `prompts/`, `templates/` - the orchestrator, executor, and evaluator contracts, role prompts, and handoff templates.
  Their role separation and evidence handoff selectively adapt the portable agent pattern from `sparesparrow/mia`; see `docs/mia-agent-patterns.md`.
- `workspace/` - a Hyprland research workspace with Perplexity and Gemini as separate web apps.
- `browser/` - Playwright MCP setup for Codex, with a safety note.
- `research/` - a dispatcher that turns a `dispatch.yaml` into research jobs.
- `orchestration/` and `project-templates/` - dependency-free discovery and rendering of repo-aware Python, embedded, and Hyprland workflow contracts, adapted from `sparesparrow/mcp-project-orchestrator`.
- `docs/no-extra-payment-audit.md` - a checklist to make sure no agent can bill you.

## Localization

The panel uses Omarchy's official `Commons.Translations` API. English is the complete source catalog in `i18n/en.json`, and Czech is the first native-review catalog in `i18n/cs.json`. Missing languages or strings fall back to English; changing **Setup > Language** updates QML bindings without restarting the shell.

Keep IDs, translation keys, commands, paths, URLs, JSON fields, and provider names stable. Translate only visible labels and explanations. Add another language as `i18n/<Omarchy-language-code>.json` with exactly the same keys as `en.json`.

The technical agent contracts remain canonical rather than being copied into 50 translated variants. Agent response-language selection should be passed separately in the task context.

## Check

```bash
./test.sh
```

This validates the manifest, parses the scripts, compiles the dispatcher, checks English/Czech catalog parity, checks that every catalog key is referenced, rejects the previous hardcoded panel labels, and requires plain-text rendering for plugin text.

The panel still needs a running Omarchy shell for live verification. Test both English and Czech, switch between them while the panel is open, and verify that longer Czech labels wrap correctly.

## Status

Nothing here has been run in a live Omarchy shell yet. The panel's QML is modeled on the shell's built-in panels but is unverified, and the research dispatcher has not been tried against the real apps. See the open issues.
