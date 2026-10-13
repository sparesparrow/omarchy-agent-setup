#!/usr/bin/env bash
# Registers the Playwright MCP server with Codex. Browser stays visible (headed)
# so you can log in or solve CAPTCHAs manually.
set -euo pipefail

command -v node >/dev/null || { echo "Node.js is required (install it first)"; exit 1; }
command -v codex >/dev/null || { echo "Codex CLI is required"; exit 1; }

codex mcp add playwright -- npx -y @playwright/mcp@latest
codex mcp list
