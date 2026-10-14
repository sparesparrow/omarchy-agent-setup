# Quota-fallback router

Decides executor and evaluator from which free quotas are used up. Matches the fallback table in `AGENTS.md` (#5).

| Situation | Executor | Evaluator |
|---|---|---|
| All available | Codex | Grok |
| Codex out | Gemini | Grok |
| Grok out | Codex | Fresh Gemini session |
| Grok and Gemini out | Codex | Claude, short diff-only review |
| Codex and Grok out | Gemini | Claude, short diff-only review |
| Codex and Gemini out, or all out | pause until quotas reset | |
| 2 failed loops | Claude replans | |

## Use
```bash
python3 router/router.py route
python3 router/router.py exhausted codex --until 2026-10-15T09:00:00+02:00
python3 router/router.py available codex
python3 router/router.py failed     # after a failed evaluator verdict
python3 router/router.py passed
```
Tests: `cd router && python3 -m unittest`

## Limits
- It only decides; it does not start agents, and it cannot detect quota use by itself. You (or a wrapper) mark an agent exhausted, optionally with a reset time.
- Free-tier limits and reset times change; check each provider's own page.
- No API keys, billing or network access are used.
- Not run yet on the Omarchy machine.
