# Nativní načítání skills

Průvodce `bash setup/github-repositories.sh` nabízí adaptéry po kroku s klony. Samostatně: `python3 setup/client-skills.py --root ~/Projects --clients omp opencode openclaw grok-build --scope both` vypíše plán bez zápisů. Teprve `--apply` žádá potvrzení každého cíle. `--roles evaluator` zvolí jedinou roli, jinak všechny tři. Profil omp s override vyžaduje `--omp-agent-dir`.

|Klient|Globální skills|Projektové skills|
|--|--|--|
|omp|`~/.omp/agent/skills`|`.omp/skills`|
|OpenCode|`~/.config/opencode/skills`|`.opencode/skills`|
|OpenClaw|`~/.openclaw/skills`|`.agents/skills` v jeho pracovním prostoru|
|Grok Build|`~/.grok/skills`|`.grok/skills`|
|Grok CLI|`~/.agents/skills`|`.agents/skills`|

OpenCode respektuje `OPENCODE_CONFIG_DIR` a `XDG_CONFIG_HOME`, OpenClaw `OPENCLAW_STATE_DIR` a Grok Build `GROK_HOME`. Variantu Groku musíš vybrat. Globálně se instalují jen tři role `omarchy-team-<role>`. Projektové skills se kopírují z již připravených `.agents/skills/omarchy-<repo>-<role>/SKILL.md`. Chybějící zdroj zablokuje plán bez zápisů.

Zápisy jsou kopie, ne symbolické odkazy. Stejné soubory se přeskočí, konflikt nebo symlink skupinu zablokuje. Nemění se configy, allowlisty, MCP, přihlášení ani procesy klientů. Načtení znamená dostupnost instrukcí, ne jejich automatické provedení. Živý test v klientech není prokázaný. Skills nejsou oprávnění ani sandbox.
