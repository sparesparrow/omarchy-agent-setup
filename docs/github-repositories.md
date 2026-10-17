# GitHub repozitáře a SSH

Spusť `bash setup/github-repositories.sh`. Průvodce pracuje s 26 repozitáři sparesparrow uvedenými v `NAMES` v Python skriptu. Tento modul zatím nemá tlačítko v panelu.

CLI: `python3 setup/github-repositories.py --root ~/Projects` pouze vypíše plán. Přidej `--search-root ~/src` (opakovatelně) pro existující klony; hloubka je 4, mění ji `--depth`. S `--apply` potvrzuješ každé klonování a instalaci skills zvlášť. Origin i kořen klonu se ověřují; více klonů se nabízí zvlášť. Symlinky, obsazené cíle a konfliktní soubory se nepřepisují. Žádný pull, stash, reset, změna origin, commit ani push.

`--ssh-setup` nabídne Ed25519 klíč s interaktivním heslem, existující ssh-agent a registraci veřejného klíče přes `gh` přihlášené jako sparesparrow. OAuth přihlášení proveď pomocí `gh auth login`. Privátní klíč se nikam neposílá, SSH config se nemění. Jiný klíč zvol `--identity /cesta` v setupu i při klonování. Bez ssh-agent může Git opakovat dotaz na heslo. Fingerprint hostitele ověř podle https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints .

Skills jsou ve `.agents/skills/omarchy-<repo>-<role>/SKILL.md` a `.claude/skills/` pro Codex a Claude. AGENTS.md a CLAUDE.md se nemění. Oborové profily jsou doporučení podle metadat, ne audit zdrojů. Další klienti vyžadují ověřený adaptér; automatické načtení se u nich neslibuje. MCP servery, oprávnění ani hlasové propojení tento modul neinstaluje. Skills nejsou izolace rolí.

Identické skills se přeskočí, konflikty odmítnou. Instalace není transakční: dříve vytvořené soubory při pozdějším konfliktu zůstanou. Nové soubory jsou lokální a necommitované; po kontrole je lze odstranit smazáním pouze uvedených omarchy-<repo>-<role> adresářů. Žádný projektový kód, závislosti ani vzdálené skills se nespouštějí.

Testy: `python3 -m unittest discover -s tests -p test_github_repositories.py -v`.
