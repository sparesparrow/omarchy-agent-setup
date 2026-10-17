# Agent tým: Orchestrator / Executor / Evaluator

Tři agenti pracují jako tým. Každý má vlastní roli, vlastní prompt a jen takové MCP nástroje, které jeho role potřebuje.

| Role | Úkol | MCP |
|---|---|---|
| Orchestrator | Prijímá úkol (hlasem nebo textem), rozděluje ho na kroky, zadává Executorovi, přijímá report Evaluatora | filesystem (read-only), github, mcp-prompts |
| Executor | Provádí kroky na počítači: soubory, příkazy, kód | filesystem (read/write), github |
| Evaluator | Kontroluje výsledek Executora proti zadání, reportuje zpět | filesystem (read-only), github (read-only), mcp-prompts |

Žádný agent nedostane MCP, které jeho role nepotřebuje.

## Instalace

```bash
bash setup/agent-team.sh
```

Skript detekuje nainstalované nástroje (omp, opencode, openclaw, claude, codex, grok) a pro každý se zeptá, zda má role a skills zapsat. Vše se ukládá do globálních adresářů, takže agenti jsou k dispozici ve všech projektech.

## Hlasové ovládání Orchestratora

Orchestrator přijímá příkazy z MIA voice console:

- `wake` — začít nový úkol
- `go-now` — spustit naplánované kroky
- `yes` — schválit report Evaluatora
- `no` — zamítnout a vrátit se k zadání
- `cancel` — zrušit aktuální úkol

## Protokol

Detailní formát zadání, reportu a schválení je v `protocol.md`.
