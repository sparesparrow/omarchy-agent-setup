#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_terminal "$@"

INFOMARCHY_URL="https://github.com/nixfred/infomarchy.git"
INFOMARCHY_ID="nixfred.infomarchy"
OMATCHY_URL="https://github.com/8bit64k/omatchy.git"
HERALD_URL="https://github.com/iamlukethedev/Herald-OS.git"
HERMES_INSTALL_URL="https://hermes-agent.nousresearch.com/install.sh"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/omarchy-agent-setup"
mkdir -p "$CACHE_DIR"

have() { command -v "$1" >/dev/null 2>&1; }

review_file() {
  if confirm "Zobrazit $1 před spuštěním?"; then
    "${PAGER:-less}" "$1" || true
  fi
}

fetch_repo() {
  if [[ -d "$2/.git" ]]; then
    git -C "$2" pull --ff-only
  else
    git clone --depth 1 "$1" "$2"
  fi
}

install_infomarchy() {
  say "Infomarchy: z tapety udělá živý přehled AI agentů (plugin od nixfred)."
  if ! have omarchy; then
    say "Příkaz omarchy nebyl nalezen. Krok přeskočen."
    return 0
  fi
  confirm "Nainstalovat Infomarchy bez zapnutí?" || return 0
  if ! omarchy plugin add "$INFOMARCHY_URL"; then
    say "Instalace pluginu selhala."
    return 0
  fi
  say "Zkontroluj kód v ~/.config/omarchy/plugins/$INFOMARCHY_ID/"
  say "Plugin vyžaduje doplňkové nastavení před zapnutím. Postup je v jeho README."
  if confirm "Zapnout Infomarchy až po kontrole kódu?"; then
    omarchy plugin enable "$INFOMARCHY_ID" || say "Zapnutí selhalo. Dokonči nastavení podle README pluginu."
  fi
}

install_hermes() {
  if have hermes; then
    say "Hermes už je nainstalovaný: $(command -v hermes)"
    return 0
  fi
  say "Hermes Agent (Nous Research). Alternativa bez skriptu: nabídka Omarchy Install > AI > Hermes Desktop."
  confirm "Stáhnout oficiální instalační skript k prohlédnutí?" || return 0
  local installer="$CACHE_DIR/hermes-install.sh"
  if ! curl -fsSL --max-time 30 "$HERMES_INSTALL_URL" -o "$installer"; then
    say "Skript se nepodařilo stáhnout."
    return 0
  fi
  review_file "$installer"
  if confirm "Spustit instalátor Hermes?"; then
    bash "$installer" || say "Instalátor skončil chybou."
  fi
  hash -r
  if have hermes; then
    if confirm "Spustit hermes setup (výběr modelu a přihlášení)?"; then
      hermes setup
    fi
  else
    say "Hermes zatím není v PATH. Otevři nový terminál a spusť hermes setup."
  fi
}

install_omatchy() {
  say "Omatchy: most témat mezi Omarchy a dashboardem Hermes (plugin + téma)."
  if ! have hermes; then
    say "Hermes nebyl nalezen v PATH. Omatchy ho potřebuje."
    confirm "Pokračovat i tak?" || return 0
  fi
  have git || { say "Chybí git."; return 0; }
  confirm "Stáhnout Omatchy k prohlédnutí?" || return 0
  local dir="$CACHE_DIR/omatchy"
  fetch_repo "$OMATCHY_URL" "$dir"
  if [[ ! -f "$dir/install.sh" ]]; then
    say "V repozitáři není install.sh. Postup je v $dir/README.md"
    return 0
  fi
  review_file "$dir/install.sh"
  if confirm "Spustit install.sh pro Omatchy?"; then
    (cd "$dir" && bash ./install.sh) || say "Instalace Omatchy selhala."
    say "Restartuj hermes dashboard a vyber téma Omatchy."
  fi
}

install_herald() {
  say "Herald OS (iamlukethedev): nezávislý projekt, není od Nous Research. Na Archu se staví z PKGBUILD."
  if ! have git || ! have makepkg; then
    say "Chybí git nebo makepkg (balík base-devel). Krok přeskočen."
    return 0
  fi
  confirm "Stáhnout zdroj Herald OS k prohlédnutí?" || return 0
  local dir="$CACHE_DIR/Herald-OS"
  fetch_repo "$HERALD_URL" "$dir"
  local pkg="$dir/packaging/arch/herald-os-bin"
  if [[ ! -f "$pkg/PKGBUILD" ]]; then
    say "PKGBUILD nenalezen v $pkg. Postup je v $dir/README.md"
    return 0
  fi
  review_file "$pkg/PKGBUILD"
  if confirm "Sestavit a nainstalovat balíček (vyžádá sudo)?"; then
    (cd "$pkg" && makepkg -si) || { say "Sestavení selhalo."; return 0; }
    if have herald-os && confirm "Spustit herald-os setup?"; then
      herald-os setup
    fi
  fi
}

say "Ekosystém Omarchy a Hermes. Každý krok se ptá zvlášť a nic se nezapne bez souhlasu."
for step in install_infomarchy install_hermes install_omatchy install_herald; do
  "$step"
done
pause_at_end
