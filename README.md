# Nastavení agentů pro Omarchy

Plugin sleduje jazyk zvolený v **Nastavení > Jazyk**. Čeština je v oficiálním registru Omarchy jako `cs`, s lokalitou `cs_CZ.UTF-8`. Texty panelu jsou v `i18n/cs.json` a načítají se přes `Commons.Translations`, stejně jako u vestavěných pluginů. Chybějící řetězec spadne na `i18n/en.json`. Logy a diagnostika zůstávají anglicky.

Při instalaci pluginu se nic dalšího nenainstaluje. Každý skript se před zápisem nebo instalací zeptá znovu.

## Instalace

```bash
omarchy-plugin-install https://github.com/sparesparrow/omarchy-agent-setup
```

Znovu načti shell, zapni **Nastavení agentů** a před spuštěním akce si projdi `Panel.qml` a `setup/`.

## Akce v panelu

- Pracovní prostor pro rešerše otevře Perplexity a Gemini vedle sebe.
- OpenClaw se nastavuje interaktivně česky a samo nic neodesílá.
- Voxtype nainstaluje diktování a model stáhne až po potvrzení.
- Katalog pluginů nainstaluje jen potvrzené pluginy a nezapne je bez dalšího souhlasu.
- Předvolby Oh My Pi připraví role pro Mia, Libertin, Human Action a další projekty. Nevybírají placený model.
- Hlasová konzole MIA posílá jen povolená tlačítka a ukazuje stav simulovaného stroje.
- Katalog promptů otevře místní prompty z `mcp-prompts` a `mcp-project-orchestrator`.
- MCP a skills zkopírují skills a volitelně zaregistrují ověřené servery. Token se nevkládá do příkazu.
- Agent tým nastaví Orchestrátora, Executora a Evaluatora pro nainstalované nástroje.
- GitHub repozitáře a SSH najdou klony, nabídnou klíč a po jednotlivých potvrzeních přidají skills.

Zástupci pro audit plateb a research dispatcher v panelu nejsou. Jejich soubory v repozitáři zůstávají.

## Hlasová konzole MIA

Posílá probuzení, jeď teď, zrušení, ano, ne, konec diktování a úroveň upovídanosti. Ukazuje stav, LED, tón, co MIA řekla a co slyšela. Zrušení nezávisí na řeči.

Neovládá auto. `/ws/voice` dnes řídí simulovaný stroj v procesu API, ne hlasový router na Pi. Konzole to říká na obrazovce.

Potřebuje zkontrolovaný checkout `sparesparrow/mia`, balíček `flatbuffers`, na Pi `VOICE_CONSOLE=1` a klíč v proměnné prostředí. Prosté `ws://` je jen pro loopback, soukromé, link-local a Tailscale adresy. Klíč jde jen v hlavičce `X-API-Key` a nikam se nezapisuje ani netiskne.

Bez terminálu:

```bash
python3 setup/mia-voice-console.py --state
python3 setup/mia-voice-console.py --command go-now
python3 setup/mia-voice-console.py --command yes --confirm yes
```

Neznámý stav povolí jen `cancel`. Konzole neposílá `Intent`, `SafetyWarning`, `IncomingMessage`, text diktování ani výsledek provedení.

## Test

```bash
./test.sh
```

Automatické testy neprokazují živé kliknutí v ploše, přepnutí jazyka, externí instalátory ani konzoli proti skutečnému Pi.
