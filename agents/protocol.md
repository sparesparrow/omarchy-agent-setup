# Protokol spolupráce agentů

## Formát zadání úkolu (Orchestrator → Executor)

```json
{
  "task_id": "uuid",
  "goal": "co má být výsledkem",
  "steps": ["krok 1", "krok 2"],
  "constraints": ["co nesmíš udělat"],
  "context": "soubory, odkazy, pozadí"
}
```

## Formát reportu (Executor → Evaluator)

```json
{
  "task_id": "uuid",
  "status": "done | partial | failed",
  "result": "co vzniklo",
  "files_changed": ["cesta/k/souboru"],
  "log": ["co se stalo"]
}
```

## Formát hodnocení (Evaluator → Orchestrator)

```json
{
  "task_id": "uuid",
  "verdict": "pass | fail | needs_work",
  "notes": ["co chybí nebo je špatně"],
  "suggestion": "co má Executor opravit"
}
```

## Pravidla

- Orchestrator nikdy nepíše soubory ani nespouští příkazy; jen plánuje a koordinuje.
- Executor nikdy nevyhodnocuje svou práci; jen ji dělá a reportuje.
- Evaluator nikdy neopravuje; jen hodnotí a navrhuje.
- `fail` nebo `needs_work` se vrací Executorovi s `suggestion`.
- `pass` se vrací Orchestratorovi jako hotový úkol.
- Hlasové `yes`/`no` od uživatele schvaluje nebo zamítá report Evaluatora před odesláním Orchestratorovi.
