#!/bin/bash
set -euo pipefail

setup_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  pwd
}

require_terminal() {
  if [[ -t 0 && -t 1 ]]; then
    return 0
  fi
  if [[ -n "${AGENT_SETUP_TERMINAL:-}" ]]; then
    echo "Interaktivní terminál se nepodařilo otevřít." >&2
    exit 1
  fi
  export AGENT_SETUP_TERMINAL=1
  local script candidate
  script=$(readlink -f "$0")
  for candidate in ${TERMINAL:-} omarchy-launch-tui ghostty kitty alacritty foot x-terminal-emulator; do
    [[ -n "$candidate" ]] || continue
    command -v "$candidate" >/dev/null 2>&1 || continue
    case "$candidate" in
      omarchy-launch-tui) exec "$candidate" bash "$script" "$@" ;;
      *) exec "$candidate" -e bash "$script" "$@" ;;
    esac
  done
  echo "Nebyl nalezen terminál. Spusť skript ručně v terminálu." >&2
  exit 1
}

say() { printf '\n%s\n' "$1"; }

confirm() {
  local answer
  read -r -p "$1 [ano/ne]: " answer
  case "${answer,,}" in
    ano|a|yes|y) return 0 ;;
    *) return 1 ;;
  esac
}

pause_at_end() { echo; read -r -p "Enter zavře toto okno..." _ || true; }
