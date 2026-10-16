# Omarchy Agent Setup

Interactive Czech setup for OpenClaw, Voxtype, community plugins, Oh My Pi presets, local prompts, and MCP skills. Nothing is installed when the plugin itself is installed.

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
- Local prompt catalog, including prompts adapted from `mcp-prompts` and `mcp-project-orchestrator`.
- MCP skills for Codex, Claude Code, and Grok. GitHub MCP registration is optional and uses an existing token variable, never a pasted token.

The payment-audit and research-dispatcher shortcuts were removed from the panel. Their files remain in the repository.

## Test

```bash
./test.sh
```

Live desktop clicks, language switching, and external installers are not proven by the automated suite.
