#!/usr/bin/env bash
# Register a visible Playwright MCP browser with its own persistent profile.
set -euo pipefail

for tool in node npx codex; do
  command -v "$tool" >/dev/null || { echo "$tool is required; install it first." >&2; exit 1; }
done

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "Run setup from the Omarchy desktop session; no display is available." >&2
  exit 1
fi

# Validate the CLI/config before changing anything. Do not overwrite an entry.
codex mcp list >/dev/null
if codex mcp get playwright >/dev/null 2>&1; then
  echo "A playwright server already exists. Review it with: codex mcp get playwright" >&2
  echo "No configuration was changed. Remove it manually only if you intend to replace it." >&2
  exit 1
fi

umask 077
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
profile="${XDG_DATA_HOME:-$HOME/.local/share}/research-profiles/playwright"
inbox="$repo_dir/.agents/research/inbox"
config="${CODEX_HOME:-$HOME/.codex}/config.toml"

if [[ -f "$config" ]]; then
  backup="$(mktemp "${config}.before-playwright.XXXXXX")"
  cp -- "$config" "$backup"
  echo "Codex configuration backup: $backup"
fi
mkdir -p -- "$profile" "$inbox"
chmod 700 -- "$profile"

codex mcp add playwright   --env PLAYWRIGHT_MCP_HEADLESS=false   --env PLAYWRIGHT_MCP_ISOLATED=false   -- npx -y @playwright/mcp@latest   --user-data-dir "$profile"   --output-dir "$inbox"
codex mcp list

echo "Registered only; browser startup and app access are not yet verified."
echo "Restart Codex and follow browser/README.md. Login and CAPTCHA handling are manual."
