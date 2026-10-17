#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_terminal "$@"

say "Agent tým: Orchestrator / Executor / Evaluator"
say "Role se ukládají globálně, aby byly k dispozici ve všech projektech."

AGENTS_DIR="$HOME/.local/share/omarchy-agent-setup/agents"
mkdir -p "$AGENTS_DIR"
cp "$(dirname "$0")/../agents/"*.md "$AGENTS_DIR/"
say "Role a protokol zkopírovány do $AGENTS_DIR"

install_claude() {
  mkdir -p "$HOME/.claude/agents" "$HOME/.claude/skills"
  cp "$AGENTS_DIR/orchestrator.md" "$HOME/.claude/agents/orchestrator.md"
  cp "$AGENTS_DIR/executor.md" "$HOME/.claude/agents/executor.md"
  cp "$AGENTS_DIR/evaluator.md" "$HOME/.claude/agents/evaluator.md"
  if [[ -f "$HOME/.claude/CLAUDE.md" ]]; then
    if ! grep -q "omarchy-agent-setup" "$HOME/.claude/CLAUDE.md"; then
      printf '\n## Agent tým\n\nRole Orchestrator, Executor a Evaluator jsou v ~/.claude/agents/. Protokol je v %s/protocol.md.\n' "$AGENTS_DIR" >> "$HOME/.claude/CLAUDE.md"
    fi
  else
    printf '# Agent tým\n\nRole Orchestrator, Executor a Evaluator jsou v ~/.claude/agents/. Protokol je v %s/protocol.md.\n' "$AGENTS_DIR" > "$HOME/.claude/CLAUDE.md"
  fi
  say "Claude Code: role v ~/.claude/agents/, CLAUDE.md aktualizován."
}

install_codex() {
  mkdir -p "$HOME/.codex" "$HOME/.agents/skills"
  cp "$AGENTS_DIR/protocol.md" "$HOME/.codex/AGENTS.md"
  say "Codex: AGENTS.md zapsán do ~/.codex/."
}

install_opencode() {
  mkdir -p "$HOME/.config/opencode/skills"
  cp "$AGENTS_DIR/protocol.md" "$HOME/.config/opencode/AGENTS.md"
  say "OpenCode: AGENTS.md zapsán do ~/.config/opencode/."
}

install_openclaw() {
  mkdir -p "$HOME/.openclaw/skills"
  cp "$AGENTS_DIR/protocol.md" "$HOME/.openclaw/AGENTS.md"
  say "OpenClaw: AGENTS.md zapsán do ~/.openclaw/."
}

install_omp() {
  mkdir -p "$HOME/.omp/agent"
  cp "$AGENTS_DIR/protocol.md" "$HOME/.omp/agent/AGENTS.md"
  say "omp: AGENTS.md zapsán do ~/.omp/agent/."
}

install_grok() {
  mkdir -p "$HOME/.grok/skills"
  cp "$AGENTS_DIR/protocol.md" "$HOME/.grok/AGENTS.md"
  say "Grok: AGENTS.md zapsán do ~/.grok/."
}

for tool in claude codex opencode openclaw omp grok; do
  if command -v "$tool" >/dev/null 2>&1; then
    if confirm "Nastavit agent tým pro $tool?"; then
      "install_$tool"
    fi
  fi
done

say "Hotovo. Role jsou globální, protokol je v $AGENTS_DIR/protocol.md."
pause_at_end
