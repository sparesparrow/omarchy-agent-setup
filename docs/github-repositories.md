# GitHub repozitáře a SSH

Spusť akci **GitHub repozitáře a SSH** v panelu, nebo `bash setup/github-repositories.sh`. Průvodce pracuje s 26 repozitáři uživatele sparesparrow uvedenými v `NAMES`.

`python3 setup/github-repositories.py --root ~/Projects` jen vypíše plán. `--search-root` lze opakovat. S `--apply` potvrzuješ každé klonování a instalaci skills zvlášť. Existující klony se neaktualizují. Žádný pull, stash, reset, změna origin, commit ani push.

`--ssh-setup` nabídne klíč Ed25519, běžící ssh-agent a registraci veřejného klíče přes `gh` přihlášené jako sparesparrow. Privátní klíč se nikam neposílá. Otisk hostitele ověř podle dokumentace GitHubu.

Skills pro Codex a Claude jsou v `.agents/skills/` a `.claude/skills/`. Existující `AGENTS.md` a `CLAUDE.md` se nemění. Nové soubory zůstanou necommitované.

Testy: `python3 -m unittest discover -s tests -p test_github_repositories.py -v`.
