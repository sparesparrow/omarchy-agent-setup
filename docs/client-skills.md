# Nativni nacitani skills

Pruvodce `bash setup/github-repositories.sh` nabizi adaptery po kroku s klony. Samostatne: `python3 setup/client-skills.py --root ~/Projects --clients omp opencode openclaw grok-build --scope both` vypise plan bez zapisu. Teprve `--apply` zada potvrzeni kazdeho cile. `--roles evaluator` zvoli jedinou roli, jinak vsechny tri. OMP profil s override vyzaduje explicitni `--omp-agent-dir`.

|Klient|Globalni skills|Projektove skills|
|--|--|--|
|omp|`~/.omp/agent/skills`|`.omp/skills`|
|OpenCode|`~/.config/opencode/skills`|`.opencode/skills`|
|OpenClaw|`~/.openclaw/skills`|`.agents/skills` v jeho workspace|
|Grok Build|`~/.grok/skills`|`.grok/skills`|
|Grok CLI|`~/.agents/skills`|`.agents/skills`|

OpenCode respektuje OPENCODE_CONFIG_DIR a XDG_CONFIG_HOME, OpenClaw OPENCLAW_STATE_DIR a Grok Build GROK_HOME. Variantu Groku musi uzivatel vybrat. Globalne se instaluji jen tri role `omarchy-team-<role>`. Projektove skills se kopiruji z jiz pripravenych `.agents/skills/omarchy-<repo>-<role>/SKILL.md`. Chybejici zdroj blokuje plan bez zapisu. Zadne configy, allowlisty, MCP, credentials ani procesy klientu se nemeni. Discovery znamena dostupnost instrukci, ne jejich automaticke provedeni. Zivy test v klientech neni prokazany.
