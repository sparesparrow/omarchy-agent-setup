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
- `AGENTS.md`, `prompts/`, `templates/` - the orchestrator, executor, and evaluator contracts, role prompts, and handoff templates.
- `workspace/` - a Hyprland research workspace with Perplexity and Gemini as separate web apps.
- `browser/` - Playwright MCP setup for Codex, with a safety note.
- `research/` - a dispatcher that turns a `dispatch.yaml` into research jobs.
- `docs/no-extra-payment-audit.md` - a checklist to make sure no agent can bill you.

## Check

```bash
./test.sh
```

Validates the manifest with `omarchy plugin validate` and checks the shell scripts. The panel itself needs a running Omarchy shell to try.

## Status

Nothing here has been run in a live Omarchy shell yet. The panel's QML is modeled on the shell's built-in panels but is unverified, and the research dispatcher has not been tried against the real apps. See the open issues.
