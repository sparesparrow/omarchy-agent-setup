#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_terminal "$@"
ROOT=$(setup_root)
say "Skills a MCP. Token sem nevkládej, jen název existující proměnné."
copy_skills() {
  local dest="$1" skill target
  mkdir -p "$dest"
  for skill in orchestrator executor evaluator czech-operator; do
    target="${dest}/${skill}"
    if [[ -e "$target" ]]; then
      say "${target} už existuje, přeskakuji."
    else
      mkdir -p "$target"
      cp "$ROOT/skills/${skill}/SKILL.md" "$target/SKILL.md"
    fi
  done
}
confirm "Skills pro Claude Code?" && copy_skills "${HOME}/.claude/skills/omarchy-agent-setup"
confirm "Skills pro Codex?" && copy_skills "${HOME}/.agents/skills/omarchy-agent-setup"
confirm "Skills pro Grok?" && copy_skills "${HOME}/.config/grok/skills/omarchy-agent-setup"
if confirm "Registrovat GitHub MCP v Codexu? Grok se neregistruje, ověřený příkaz nemám."; then
  read -r -p "Název proměnné s tokenem: " token_var
  if [[ "$token_var" =~ ^[A-Z_][A-Z0-9_]*$ ]] && command -v codex >/dev/null 2>&1; then
    codex mcp add github --url https://api.githubcopilot.com/mcp/ --bearer-token-env-var "$token_var"
  else
    say "MCP jsem nepřidal."
  fi
fi
say "Claude Code MCP registruji až po kontrole příkazu claude mcp add --help."
if command -v claude >/dev/null 2>&1 && confirm "Ukázat nápovědu claude mcp add?"; then
  claude mcp add --help || true
fi
pause_at_end
