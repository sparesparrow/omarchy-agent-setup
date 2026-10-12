#!/usr/bin/env bash
# Opens Perplexity and Gemini as separate web apps with isolated browser profiles
# and switches to the research workspace. Run on the Omarchy machine.
set -euo pipefail

WS="${RESEARCH_WS:-4}"
PROFILES="$HOME/.local/share/research-profiles"
mkdir -p "$PROFILES/perplexity" "$PROFILES/gemini"

hyprctl dispatch workspace "$WS"

omarchy-launch-webapp "https://www.perplexity.ai/" \
  --user-data-dir="$PROFILES/perplexity" &
sleep 2
omarchy-launch-webapp "https://gemini.google.com/" \
  --user-data-dir="$PROFILES/gemini" &
wait
