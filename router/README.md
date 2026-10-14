# Quota-fallback router

Decides executor and evaluator from which free quotas are used up. Matches the fallback table in `AGENTS.md` (#5).

Claude is never picked as evaluator automatically (#35). When no other evaluator is left, the router answers `ask` and waits for you.

| Situation | Executor | Evaluator |
|---|---|---|
| All available | Codex | Grok |
| Codex out | Gemini | Grok |
| Grok out | Codex | Fresh Gemini session |
| Grok and Gemini out | Codex | `ask`: pause, or Claude diff-only review after `approve claude-eval` |
| Codex and Grok out | Gemini | `ask`: pause, or Claude diff-only review after `approve claude-eval` |
| Codex and Gemini out, or all out | pause until quotas reset | |
| 2 failed loops | Claude replans (planning, not evaluation) | |

## Use
```bash
python3 router/router.py route
python3 router/router.py exhausted codex --until 2026-10-15T09:00:00+02:00
python3 router/router.py available codex
python3 router/router.py failed     # after a failed evaluator verdict
python3 router/router.py passed     # also clears a pending Claude approval
python3 router/router.py approve claude-eval   # one-time OK; consumed by the next route
```
Tests: `cd router && python3 -m unittest`

## Claude approval
When `route` returns `"action": "ask"`, choose to pause or run `approve claude-eval`. The next `route` then returns `claude-diff-only` once and clears the approval. `status` does not consume it, `passed` clears it, and `replan` is not affected.

## Limits
- It only decides; it does not start agents, and it cannot detect quota use by itself. You (or a wrapper) mark an agent exhausted, optionally with a reset time.
- Free-tier limits and reset times change; check each provider's own page.
- No API keys, billing or network access are used.
- Not run yet on the Omarchy machine.
