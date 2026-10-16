# Omarchy Agent Setup

Interactive Czech setup for OpenClaw, Voxtype, community plugins, Oh My Pi presets, local prompts, MCP skills, and a MIA voice console. Nothing is installed when the plugin itself is installed.

## Install

```bash
omarchy-plugin-install https://github.com/sparesparrow/omarchy-agent-setup
```

Reload the shell, enable **Agent Setup**, and review `Panel.qml` and `setup/` before running an action.

## Panel actions

- Research workspace.
- OpenClaw orchestrator, interactive in Czech. It can run the official wizard only after you confirm.
- Voxtype setup. Model download happens only after confirmation.
- Plugin catalog. Each plugin is installed only after a separate yes and is not enabled unless you confirm that too.
- Oh My Pi presets for Mia, Libertin, Human Action, Omarchy Steward, and general software. Presets do not select a paid model.
- MIA voice console, a terminal client for the `/ws/voice` WebSocket of a MIA API. See the section below for what it does and does not control.
- Local prompt catalog, including prompts adapted from `mcp-prompts` and `mcp-project-orchestrator`.
- MCP skills for Codex, Claude Code, and Grok. GitHub MCP registration is optional and uses an existing token variable, never a pasted token.

The payment-audit and research-dispatcher shortcuts were removed from the panel. Their files remain in the repository.

## MIA voice console

It sends wake, go now, cancel, yes, no, end dictation, and the verbosity setting, and shows the machine state, the LED and tone cue, what MIA said, and what it heard. Cancel never depends on speech.

It does not control the car. In MIA today, `/ws/voice` drives a simulated voice state machine inside the API process, not the voice router that runs on the Pi. The console says so on screen.

Requirements:

- A checkout of `sparesparrow/mia` that you have reviewed. The console imports MIA's own codec from it, so that code runs on your machine.
- The Python package `flatbuffers`.
- `VOICE_CONSOLE=1` on the Pi and an API key in an environment variable. A read-scoped key is enough to press the buttons.

Safety: plain `ws://` is accepted only for loopback, private, link-local, and Tailscale addresses; use `wss://` otherwise. The key is read from a variable you name, sent only as the `X-API-Key` header, and never written to disk or printed. Text received from the server has control characters replaced before it is shown.

## Test

```bash
./test.sh
```

Live desktop clicks, language switching, external installers, and the MIA console against a real Pi are not proven by the automated suite. The console tests use a stand-in codec and a local test server.
